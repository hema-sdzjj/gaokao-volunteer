#!/usr/bin/env python3
"""V9: P1 — 专业一句话描述 + 专业搜索排序 + 志愿数量建议"""
import json, re

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html') as f:
    html = f.read()

# ===== 1. 专业一句话描述 =====
MAJOR_ONELINERS = {
    "计算机科学与技术": "每天写代码、调bug、学新技术，大部分时间对着屏幕",
    "软件工程": "和计算机类似，但更偏工程化开发，团队协作多",
    "通信工程": "研究信号传输，从5G到WiFi，数学要求高",
    "临床医学": "背不完的书+值不完的班，但救死扶伤的成就感无可替代",
    "口腔医学": "动手操作多，不需要值大夜班，市场化程度高",
    "法学": "背法条+写文书+辩论，法考是必须翻过的大山",
    "经济学": "分析数据+理解市场，很多时间在看报告和做模型",
    "会计学": "做账+审计+报税，细致活，CPA是分水岭",
    "机械工程": "设计+制造+画图，传统工科的基石",
    "车辆工程": "研究汽车，新能源和自动驾驶是当下热点",
    "土木工程": "下工地+画图纸+做预算，风吹日晒是常态",
    "电气工程及其自动化": "和电打交道，强电（电网）稳定，弱电（电子）灵活",
    "自动化": "让机器自己干活，控制理论+编程+硬件都要会",
    "英语": "学语言+文学+翻译，不像十年前那么好找工作了",
    "数学与应用数学": "证明+计算+建模，万物皆可数学，转行万能跳板",
    "社会工作": "帮弱势群体解决问题，写个案+跑社区，钱少但有意义",
    "信息管理与信息系统": "管IT系统+分析数据，介于计算机和管理的交叉地带",
}

# ===== 2. 注入专业一句话描述数据 =====
oneliner_js = "const MAJOR_ONELINERS = " + json.dumps(MAJOR_ONELINERS, ensure_ascii=False) + ";"
html = html.replace("const TREND_DATA = ", oneliner_js + "\nconst TREND_DATA = ", 1)

# ===== 3. 在推荐卡片中加入一句话描述 =====
# 在 major_name 后面加入描述
old_major_display = '''<h3 class="font-semibold text-gray-800 cursor-pointer hover:text-blue-600 underline decoration-dotted" onclick="openSchoolModal(\'${item.school_name}\')">${item.school_name} · ${item.major_name}</h3>'''
new_major_display = '''<h3 class="font-semibold text-gray-800 cursor-pointer hover:text-blue-600 underline decoration-dotted" onclick="openSchoolModal(\'${item.school_name}\')">${item.school_name} · ${item.major_name}</h3>
          <p class="text-xs text-gray-400 mt-0.5 italic">${MAJOR_ONELINERS[item.major_name]||\'\'}</p>'''

html = html.replace(old_major_display, new_major_display)

# ===== 4. 专业搜索排序 — 新增一个搜索框在策略标签旁边 =====
major_search_html = '''
    <div class="flex gap-3 mb-5 items-end">
      <div>
        <label class="text-xs text-gray-500 mb-1 block">🔍 按专业搜索（输入你想学的专业）</label>
        <input type="text" id="major-search" placeholder="例: 计算机" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-48 focus:ring-2 focus:ring-blue-500 outline-none" oninput="filterByMajor()">
      </div>
      <button onclick="clearMajorFilter()" class="text-xs text-gray-400 hover:text-blue-500 hidden" id="clear-major-filter">清除</button>
      <span class="text-xs text-gray-400 hidden" id="major-filter-count"></span>
    </div>
'''
html = html.replace('<div class="flex gap-3 mb-5" id="strategy-tabs">', major_search_html + '\n<div class="flex gap-3 mb-5" id="strategy-tabs">')

# ===== 5. 专业搜索逻辑 =====
major_filter_js = '''
function filterByMajor() {
  var q = document.getElementById('major-search').value.trim().toLowerCase();
  var clearBtn = document.getElementById('clear-major-filter');
  var countEl = document.getElementById('major-filter-count');
  if (!q) { clearBtn.classList.add('hidden'); countEl.classList.add('hidden'); showTab(state.activeTab); return; }
  clearBtn.classList.remove('hidden');
  countEl.classList.remove('hidden');

  // 在所有推荐中搜索
  var results = [];
  ['reach','match','safety'].forEach(function(k){
    (state.recs[k]||[]).forEach(function(r){
      if (r.major_name.toLowerCase().includes(q) || r.school_name.toLowerCase().includes(q)) {
        results.push(r);
      }
    });
  });

  countEl.textContent = '找到 '+results.length+' 个匹配（按概率排序）';
  results.sort(function(a,b){return b.probability - a.probability;});

  // 渲染结果（不分冲稳保标签）
  document.querySelectorAll('.strategy-tab').forEach(function(t){t.classList.remove('tab-active');});
  var container = document.getElementById('rec-list');
  if (!results.length) {
    container.innerHTML = '<p class="text-center text-gray-400 py-8">没有匹配「'+q+'」的专业，换个关键词试试</p>';
    return;
  }
  renderFilteredResults(results);
}

function renderFilteredResults(items) {
  var container = document.getElementById('rec-list');
  container.innerHTML = items.map(function(item,idx){
    var probPct = (item.probability*100).toFixed(0);
    var probColor = item.probability>=0.8?'bg-green-500':item.probability>=0.5?'bg-yellow-500':'bg-red-400';
    var tag = item.strategy==='reach'?'tag-reach':item.strategy==='match'?'tag-match':'tag-safety';
    var tagLabel = item.strategy==='reach'?'冲':item.strategy==='match'?'稳':'保';
    var inVol = state.volunteers.some(function(v){return v.id===item.id;});
    var hist = (item.min_rank_history||[]).map(function(r,i){return [2023,2024,2025][i]+'年:'+(r?r.toLocaleString()+'名':'--');}).join(' · ');
    var trendHtml='';
    if (TREND_DATA && TREND_DATA[item.major_name]) {
      var t=TREND_DATA[item.major_name];
      trendHtml='<span class="text-xs">'+(t.trend_4yr.indexOf('强劲')>=0?'🔥':t.trend_4yr.indexOf('增长')>=0?'📈':t.trend_4yr.indexOf('下行')>=0||t.trend_4yr.indexOf('下降')>=0?'⚠️':'➡️')+'</span>';
    }
    var warnHtml='';
    if (TREND_DATA && TREND_DATA[item.major_name]) {
      var tw=TREND_DATA[item.major_name];
      if (tw.saturation==='极高'||tw.ai_resilience==='极低'||tw.trend_4yr.indexOf('下行')>=0||tw.trend_4yr.indexOf('下降')>=0) {
        warnHtml='<span class="bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold animate-pulse">⚠️ 该专业就业市场正在萎缩，请谨慎考虑</span>';
      }
    }
    var empSummary='';
    if (item.employment) {
      empSummary='<div class="mt-2 bg-gray-50 rounded-lg p-2 text-xs"><div class="flex flex-wrap gap-3">'+
        '<span>💰 起薪: ¥'+(item.employment.salary_start/1000).toFixed(0)+'K</span>'+
        '<span>'+trendHtml+'</span>'+
        (TREND_DATA&&TREND_DATA[item.major_name]?'<span>饱和: '+TREND_DATA[item.major_name].saturation+'</span>':'')+
        '<button onclick="toggleEmpDetail(this)" class="text-blue-500 hover:text-blue-700 ml-auto">展开详情 ▾</button>'+
        '</div><div class="emp-detail hidden mt-2 pt-2 border-t border-gray-200">'+
        '<p>💼 5年: ¥'+item.employment.salary_5yr.toLocaleString()+' | 10年+: ¥'+item.employment.salary_10yr.toLocaleString()+'</p>'+
        '<p>🏢 '+Object.entries(item.employment.industries).map(function(e){return e[0]+' '+e[1]+'%';}).join(' | ')+'</p>'+
        '<p>🌆 '+Object.entries(item.employment.cities).map(function(e){return e[0]+' '+e[1]+'%';}).join(' | ')+'</p>'+
        '<p>🏭 '+item.employment.employers+'</p>'+
        '<p class="text-gray-500 mt-1">💬 '+item.employment.note+'</p>'+
        '<p class="text-gray-400 mt-1">📊 薪资趋势: '+item.employment.salary_trend+'</p>'+
        (function(){var t=TREND_DATA[item.major_name];if(!t)return'';return'<div class="mt-2 bg-gradient-to-r from-amber-50 to-blue-50 rounded-lg p-2"><p class="font-medium text-amber-800">🔮 2030年展望</p><p>📈 '+t.outlook_2030+'</p><p>🤖 AI抵抗力: '+t.ai_resilience+'</p></div>';})()+
        '</div></div>';
    }
    return '<div class="card p-4 hover:shadow-md transition-all animate-in '+(inVol?'ring-2 ring-blue-300':'')+'">'+
      '<div class="flex items-start justify-between"><div class="flex-1">'+
      '<div class="flex items-center gap-2 mb-1"><span class="'+tag+'">'+tagLabel+'</span><span class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">'+item.school_level+'</span><span class="text-xs text-gray-400">'+item.school_province+'·'+item.school_city+'</span>'+warnHtml+(inVol?'<span class="text-xs text-blue-500">✅ 已添加</span>':'')+'</div>'+
      '<h3 class="font-semibold text-gray-800 cursor-pointer hover:text-blue-600 underline decoration-dotted" onclick="openSchoolModal(\''+item.school_name+'\')">'+item.school_name+' · '+item.major_name+'</h3>'+
      '<p class="text-xs text-gray-400 mt-0.5 italic">'+(MAJOR_ONELINERS[item.major_name]||'')+'</p>'+
      '<div class="flex items-center gap-4 mt-2 text-sm text-gray-500"><span>选科: <strong>'+(item.subject_req||'不限')+'</strong></span><span>预测位次: <strong>'+Math.round(item.predicted_rank).toLocaleString()+'名</strong></span><span>招生: <strong>'+item.quota+'人</strong></span>'+(item.tuition?'<span>学费: <strong>'+item.tuition+'/年</strong></span>':'')+'</div>'+
      '<div class="text-xs text-gray-400 mt-1">近3年位次: '+hist+'</div>'+empSummary+
      '</div><div class="flex flex-col items-end gap-2 ml-4"><div class="text-center"><p class="text-2xl font-bold '+(item.probability>=0.8?'text-green-600':item.probability>=0.5?'text-yellow-600':'text-red-500')+'">'+probPct+'%</p><p class="text-xs text-gray-400">录取概率</p></div>'+
      '<div class="w-24 prob-bar"><div class="prob-fill '+probColor+'" style="width:'+probPct+'%"></div></div>'+
      '<button onclick="addVol(\''+item.id+'\')" class="text-sm px-3 py-1.5 rounded-lg '+(inVol?'bg-gray-100 text-gray-400 cursor-not-allowed':'bg-blue-50 text-blue-600 hover:bg-blue-100')+' transition" '+(inVol?'disabled':'')+'>'+(inVol?'已添加':'+ 加入志愿表')+'</button></div></div></div>';
  }).join('');
}

function clearMajorFilter() {
  document.getElementById('major-search').value = '';
  document.getElementById('clear-major-filter').classList.add('hidden');
  document.getElementById('major-filter-count').classList.add('hidden');
  showTab(state.activeTab);
}
'''
html = html.replace('// ==================== UI渲染 ====================', major_filter_js + '\n// ==================== UI渲染 ====================')

# ===== 6. 志愿数量建议 =====
# 在志愿表管理区加入智能建议
vol_advice_html = '''
    <!-- 志愿数建议条 -->
    <div id="vol-advice" class="bg-blue-50 rounded-lg p-3 mb-4 text-sm hidden">
      <span class="font-medium text-blue-800">💡 志愿数建议：</span>
      <span id="vol-advice-text" class="text-blue-700"></span>
    </div>
'''
html = html.replace('<div id="vol-stats"', vol_advice_html + '\n<div id="vol-stats"')

vol_advice_js = '''
function updateVolAdvice() {
  var n = state.volunteers.length;
  var reach = state.volunteers.filter(function(v){return v.strategy==='reach'||v.strategy==='冲';}).length;
  var match = state.volunteers.filter(function(v){return v.strategy==='match'||v.strategy==='稳';}).length;
  var safety = state.volunteers.filter(function(v){return v.strategy==='safety'||v.strategy==='保';}).length;
  var advice = document.getElementById('vol-advice');
  var text = document.getElementById('vol-advice-text');
  if (!advice || !text) return;

  if (n === 0) { advice.classList.add('hidden'); return; }
  advice.classList.remove('hidden');

  var msgs = [];
  if (safety < 20) msgs.push('保底太少，建议至少20个稳保志愿防止滑档');
  if (reach > 20) msgs.push('冲的有点多（'+reach+'个），96个志愿不必全压在低概率上');
  if (match < 30 && n > 40) msgs.push('稳妥志愿不足，建议增加到30个以上');
  if (n < 30) msgs.push('还有'+(96-n)+'个空位，充分利用96个志愿空间');
  if (msgs.length === 0 && n >= 30) msgs.push('结构看起来不错 👍 — 冲'+reach+'·稳'+match+'·保'+safety+'，梯度合理');
  if (msgs.length === 0) msgs.push('再增加一些志愿会更稳妥');

  text.textContent = msgs.join('；');
}
'''
html = html.replace('// ==================== 志愿表管理 ====================', vol_advice_js + '\n// ==================== 志愿表管理 ====================')

# ===== 7. 在 renderVolTable 最后调用 updateVolAdvice =====
old_render_end = '''document.getElementById('my-vol-cnt').textContent = state.volunteers.length;
  document.getElementById('vol-badge').textContent = state.volunteers.length;'''
new_render_end = '''document.getElementById('my-vol-cnt').textContent = state.volunteers.length;
  document.getElementById('vol-badge').textContent = state.volunteers.length;
  updateVolAdvice();'''
html = html.replace(old_render_end, new_render_end, 1)  # 只替换第一个

# ===== 8. 在removeVol/clearVolunteers中也调用 =====
html = html.replace('function clearVolunteers() { if(!confirm(\'确定清空？\')) return; state.volunteers=[]; saveToStorage(); showTab(state.activeTab); renderVolTable(); document.getElementById(\'analysis-panel\').classList.add(\'hidden\'); }',
                     'function clearVolunteers() { if(!confirm(\'确定清空？\')) return; state.volunteers=[]; saveToStorage(); showTab(state.activeTab); renderVolTable(); document.getElementById(\'analysis-panel\').classList.add(\'hidden\'); updateVolAdvice(); }')

html = html.replace('saveToStorage();\n  showTab(state.activeTab);\n  renderVolTable();\n  document.getElementById(\'analysis-panel\').classList.add(\'hidden\');\n}',
                     'saveToStorage();\n  showTab(state.activeTab);\n  renderVolTable();\n  document.getElementById(\'analysis-panel\').classList.add(\'hidden\');\n  updateVolAdvice();\n}')

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html', 'w') as f:
    f.write(html)

print(f'Done. {len(html)} chars ({len(html.encode())/1024:.0f} KB)')
