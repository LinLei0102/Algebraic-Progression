/* Algebraic Progression 简体中文运行时引擎
 * 只在 localStorage.APLang === 'zh' 时激活；英文模式完全透传原版。
 * 依赖：先加载 i18n/dict.js（window.AP_ZH_DATA）。
 */
(function () {
  'use strict';

  var KEY = 'APLang';
  var data = window.AP_ZH_DATA || { exact: {}, patterns: [], phrases: [] };
  var lang = localStorage.getItem(KEY) || 'zh';
  var exact = data.exact || {};
  var exactCI = Object.create(null);
  Object.keys(exact).forEach(function (k) {
    var lk = k.toLowerCase();
    if (!(lk in exactCI)) exactCI[lk] = exact[k];
  });
  var patterns = (data.patterns || []).map(function (p) {
    // 以 {{0}} 开头的模式原本用 ([\\s\\S]*?) 当首个通配，会把 "Currently: 1.00x"
    // 这类展示前缀整个吞进捕获组，导致前缀保持英文。首个通配只允许数字式前缀。
    var restrictFirst = /^\{\{0\}\}/.test(p.en);
    var src = p.en.split(/(\{\{\d+\}\})/).map(function (part) {
      if (/^\{\{\d+\}\}$/.test(part)) {
        if (restrictFirst && part === '{{0}}') return '([0-9.,+\\-eE^%\\s]*?)';
        return '([\\s\\S]*?)';
      }
      return part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }).join('');
    try { return { re: new RegExp('^' + src + '$'), zh: p.zh }; }
    catch (e) { return null; }
  }).filter(Boolean);

  // 短语表：按长度降序，只用于整串未命中的动态文本。
  var phrases = (data.phrases || []).slice().sort(function (a, b) {
    return b.en.length - a.en.length;
  });
  var phraseRe = phrases.length ? new RegExp(
    phrases.map(function (p) {
      var s = p.en.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return /[A-Za-z]$/.test(p.en) ? '(?<![A-Za-z])' + s + '(?![A-Za-z])' : s;
    }).join('|'), 'g'
  ) : null;
  var phraseMap = Object.create(null);
  phrases.forEach(function (p) { phraseMap[p.en] = p.zh; });

  var residuals = (window.__AP_RESIDUALS__ = window.__AP_RESIDUALS__ || {});
  var SKIP_NODES = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1 };
  var ATTRS = { title: 1, placeholder: 1, alt: 1, 'aria-label': 1, 'data-text': 1, label: 1, content: 1 };
  var CODE_HINT = /(?:=>|\bfunction\b|\breturn\b|\bvar\b|\blet\b|\bconst\b|\bnew Decimal\b|localStorage|player\.|tmp\.|window\.|document\.|\bconsole\.|\bhttp|\.js\b|\.png\b|<script|class=|className=|data-notify)/;

  // Vue 2 更新文本 vnode 时直接写 elem.data（见 vendor/vue-2.6.12.min.js 的 setTextContent），
  // textContent / createTextNode 钩子都拦不到，必须补 CharacterData.data / Node.nodeValue 钩子。
  var rawDataSetter = null;
  var rawNodeValueSetter = null;
  var inNodeWrite = false;

  function writableText(node) {
    return node && node.nodeType === 3 &&
      !(node.parentNode && SKIP_NODES[node.parentNode.nodeName]);
  }
  function translateForWrite(node, v) {
    if (typeof v !== 'string' || inNodeWrite || !writableText(node)) return v;
    return translate(v);
  }
  function hookedNodeWrite(node, v, rawSetter) {
    if (inNodeWrite) return rawSetter.call(node, v);
    var out = translateForWrite(node, v);
    inNodeWrite = true;
    try { return rawSetter.call(node, out); }
    finally { inNodeWrite = false; }
  }
  function writeTextDirect(node, v) {
    if (rawDataSetter) rawDataSetter.call(node, v); else node.nodeValue = v;
  }

  function isChinese(s) { return /[\u4e00-\u9fff]/.test(s); }
  function hasEnglish(s) { return /[A-Za-z]{3}/.test(s); }

  function noteResidual(s) {
    if (!hasEnglish(s) || isChinese(s) || CODE_HINT.test(s)) return;
    if (s.length < 4 || s.length > 300) return;
    if (/\{\{/.test(s)) return; // Vue 模板源码片段，非运行时显示文本
    residuals[s] = (residuals[s] || 0) + 1;
  }

  function byPhrases(s) {
    // 允许对「半英半中」节点继续替换：Vue 把静态译文与动态插值合并在同一文本节点，
    // 若因含中文就跳过，插值里残留的英文（如 "0 Buildings."）将永远无法翻译。
    if (!phraseRe || CODE_HINT.test(s) || /[{}]/.test(s)) return s;
    var out = s.replace(phraseRe, function (m) { return phraseMap[m] || m; });
    return out === s ? s : out;
  }

  function translate(s) {
    if (lang !== 'zh' || typeof s !== 'string' || !s) return s;
    if (isChinese(s) && !hasEnglish(s)) return s;
    if (Object.prototype.hasOwnProperty.call(exact, s)) return exact[s];
    var t = s.trim();
    if (t !== s && Object.prototype.hasOwnProperty.call(exact, t)) {
      var m = s.match(/^\s*/)[0], n = s.match(/\s*$/)[0];
      return m + exact[t] + n;
    }
    if (Object.prototype.hasOwnProperty.call(exactCI, t.toLowerCase())) {
      return exactCI[t.toLowerCase()];
    }
    for (var i = 0; i < patterns.length; i++) {
      var mm = s.match(patterns[i].re);
      if (mm) {
        var zh = patterns[i].zh;
        for (var j = mm.length - 1; j >= 1; j--) {
          zh = zh.split('{{' + (j - 1) + '}}').join(mm[j]);
        }
        return zh;
      }
    }
    var out = byPhrases(s);
    if (out !== s) return out;
    noteResidual(s);
    return s;
  }

  // HTML 串在解析成 DOM 前先做整串精确翻译，避免带 <sup>/<span> 的新闻整句
  // 被拆成多个文本节点后永远匹配不上词典里的完整条目。
  function translateHTMLString(s) {
    if (lang !== 'zh' || typeof s !== 'string' || !s) return s;
    if (Object.prototype.hasOwnProperty.call(exact, s)) return exact[s];
    var t = s.trim();
    if (t !== s && Object.prototype.hasOwnProperty.call(exact, t)) {
      var m = s.match(/^\s*/)[0], n = s.match(/\s*$/)[0];
      return m + exact[t] + n;
    }
    return s;
  }

  function translateAttr(el, name) {
    if (!ATTRS[name]) return;
    var v = el.getAttribute(name);
    if (v) {
      var t = translate(v);
      if (t !== v) el.setAttribute(name, t);
    }
  }

  function translateSubtree(root) {
    if (!root || !root.querySelectorAll) return;
    if (root.nodeType === 1 && SKIP_NODES[root.nodeName]) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, null, false);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      if (node.nodeType === 3) {
        var parent = node.parentNode;
        if (!parent || SKIP_NODES[parent.nodeName]) return;
        var v = node.nodeValue;
        if (!v) return;
        var t = translate(v);
        if (t !== v) writeTextDirect(node, t);
      } else if (node.nodeType === 1 && !SKIP_NODES[node.nodeName]) {
        Object.keys(ATTRS).forEach(function (a) { translateAttr(node, a); });
      }
    });
  }

  if (lang === 'zh') {
    // 运行时文本节点写入钩子：Vue 直接写 data，原生 API 也可能写 nodeValue。
    var dataDesc = Object.getOwnPropertyDescriptor(CharacterData.prototype, 'data');
    if (dataDesc && dataDesc.set) {
      rawDataSetter = dataDesc.set;
      Object.defineProperty(CharacterData.prototype, 'data', {
        configurable: true,
        enumerable: true,
        get: dataDesc.get,
        set: function (v) { return hookedNodeWrite(this, v, rawDataSetter); }
      });
    }
    var nodeValueDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'nodeValue');
    if (nodeValueDesc && nodeValueDesc.set) {
      rawNodeValueSetter = nodeValueDesc.set;
      Object.defineProperty(Node.prototype, 'nodeValue', {
        configurable: true,
        enumerable: true,
        get: nodeValueDesc.get,
        set: function (v) { return hookedNodeWrite(this, v, rawNodeValueSetter); }
      });
    }

    var textSetter = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent').set;
    Object.defineProperty(Node.prototype, 'textContent', {
      configurable: true,
      enumerable: true,
      get: Object.getOwnPropertyDescriptor(Node.prototype, 'textContent').get,
      set: function (v) {
        if (this.nodeType === 3 || (this.nodeType === 1 && !SKIP_NODES[this.nodeName])) {
          v = translate(v);
        }
        inNodeWrite = true;
        try { return textSetter.call(this, v); }
        finally { inNodeWrite = false; }
      }
    });

    var htmlSetter = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML').set;
    Object.defineProperty(Element.prototype, 'innerHTML', {
      configurable: true,
      enumerable: true,
      get: Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML').get,
      set: function (v) {
        v = translateHTMLString(v);
        inNodeWrite = true;
        try { htmlSetter.call(this, v); }
        finally { inNodeWrite = false; }
        if (!SKIP_NODES[this.nodeName]) translateSubtree(this);
      }
    });

    var outerSetter = Object.getOwnPropertyDescriptor(Element.prototype, 'outerHTML').set;
    Object.defineProperty(Element.prototype, 'outerHTML', {
      configurable: true,
      enumerable: true,
      get: Object.getOwnPropertyDescriptor(Element.prototype, 'outerHTML').get,
      set: function (v) {
        v = translateHTMLString(v);
        inNodeWrite = true;
        try { outerSetter.call(this, v); }
        finally { inNodeWrite = false; }
        if (this.parentNode) translateSubtree(this.parentNode);
      }
    });

    var origSetAttribute = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function (name, value) {
      if (ATTRS[name] && typeof value === 'string') value = translate(value);
      return origSetAttribute.call(this, name, value);
    };

    var origCreateTextNode = document.createTextNode.bind(document);
    document.createTextNode = function (v) {
      v = translate(v);
      inNodeWrite = true;
      try { return origCreateTextNode(v); }
      finally { inNodeWrite = false; }
    };

    var origInsertAdjacentHTML = Element.prototype.insertAdjacentHTML;
    Element.prototype.insertAdjacentHTML = function (pos, html) {
      html = translateHTMLString(html);
      inNodeWrite = true;
      try { origInsertAdjacentHTML.call(this, pos, html); }
      finally { inNodeWrite = false; }
      translateSubtree(this);
    };

    var titleDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'title');
    if (titleDesc && titleDesc.set) {
      Object.defineProperty(Document.prototype, 'title', {
        configurable: true,
        enumerable: true,
        get: titleDesc.get,
        set: function (v) { titleDesc.set.call(this, translate(v)); }
      });
    }

    var origAlert = window.alert, origConfirm = window.confirm, origPrompt = window.prompt;
    window.alert = function (m) { return origAlert(translate(String(m))); };
    window.confirm = function (m) { return origConfirm(translate(String(m))); };
    window.prompt = function (m, d) { return origPrompt(translate(String(m)), d); };

    function initialPass() {
      translateSubtree(document.documentElement);
      var t = document.getElementById('langToggle');
      if (t) t.textContent = '语言 / Language: 中文';
      var f = document.getElementById('langToggleFloat');
      if (f) f.textContent = '中文 / EN';
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () { setTimeout(initialPass, 0); });
    } else {
      setTimeout(initialPass, 0);
    }
    window.addEventListener('load', function () {
      setTimeout(initialPass, 50);
      // Vue 在 load 时重新编译 #app，之前注入的按钮会被覆盖，需再次注入。
      setTimeout(injectControls, 120);
    });
  }

  // 设置面板按钮由 Vue 的 v-if 动态创建，出现时同步标签文本。
  function syncToggleLabel() {
    var btn = document.getElementById('langToggle');
    if (btn) {
      var label = lang === 'zh' ? '语言 / Language: 中文' : '语言 / Language: English';
      if (btn.textContent !== label) btn.textContent = label;
    }
  }
  var obs = new MutationObserver(syncToggleLabel);
  obs.observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('load', function () { setTimeout(syncToggleLabel, 150); });

  window.APLang = lang;
  window.toggleLanguage = function () {
    localStorage.setItem(KEY, lang === 'zh' ? 'en' : 'zh');
    location.reload();
  };

  // 语言切换按钮：
  // - index.html：设置面板里的按钮已写死在模板中（#tab2disp 内），无需动态注入，
  //   更不能在右上角加浮动按钮——那会与设置面板的按钮重复。
  // - changelog.html：没有游戏设置面板，才用右上角浮动按钮。
  function injectControls() {
    var isGame = !!document.getElementById('app');
    if (isGame) {
      // 清理可能由旧版本注入的浮动按钮，避免重复。
      var stale = document.getElementById('langToggleFloat');
      if (stale && stale.parentNode) stale.parentNode.removeChild(stale);
      return;
    }
    if (!document.getElementById('langToggleFloat')) {
      var float = document.createElement('button');
      float.id = 'langToggleFloat';
      float.onclick = function () { window.toggleLanguage(); };
      float.textContent = lang === 'zh' ? '中文 / EN' : 'EN / 中文';
      float.title = '切换语言 / Switch language';
      float.style.cssText = 'position:fixed;top:6px;right:6px;z-index:99999;padding:4px 8px;';
      document.body.appendChild(float);
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectControls);
  } else {
    injectControls();
  }
})();
