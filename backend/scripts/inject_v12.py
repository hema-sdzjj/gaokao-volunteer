#!/usr/bin/env python3
"""V12: 全部剩余优化 — 信息分层+分档策略+模块打通+分歧化解+院校气质+经济账+冲稳保建议"""
import json, re

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html') as f:
    html = f.read()

# ===== 1. 院校气质描述 =====
SCHOOL_CHARACTER = {
    "北京大学": "自由包容，思想激荡，未名湖畔的人文气息浓厚",
    "清华大学": "务实严谨，工科霸主，'自强不息厚德载物'深入骨髓",
    "复旦大学": "精致优雅，海派文化，自由而无用的灵魂",
    "上海交通大学": "锐意进取，工科务实派，闵行荒郊野岭但就业硬核",
    "浙江大学": "创新冒险，创业氛围极浓，杭州互联网圈的黄埔军校",
    "南京大学": "低调内敛，学风淳朴，基础学科功底扎实",
    "武汉大学": "浪漫自由，珞珈山上樱花树下，中国最美大学之一",
    "华中科技大学": "踏实勤奋，工科见长，武汉'关山口男子职业技术学院'",
    "山东大学": "厚重扎实，儒学底蕴，山东娃的清华北大",
    "中国海洋大学": "海洋特色鲜明，青岛海滨的学术灯塔",
    "哈尔滨工业大学": "硬核工科，冰城锻造，规格严格功夫到家",
    "西安交通大学": "西迁精神，电气机械王者，低调的实力派",
    "中国科学技术大学": "纯粹科研，科学家摇篮，合肥安静读书的好地方",
    "中国人民大学": "人文社科殿堂，'第二党校'，体制内快车道",
    "中山大学": "岭南第一学府，自由开放，广深就业直通车",
    "厦门大学": "最美海景校园，会计学圣地，适合文艺青年",
    "南开大学": "允公允能，低调实力派，周恩来总理母校",
}

# 将气质描述注入院校详情弹窗
char_js = "const SCHOOL_CHARACTER = " + json.dumps(SCHOOL_CHARACTER, ensure_ascii=False) + ";"
html = html.replace("const EXIT_STRATEGY = ", char_js + "\nconst EXIT_STRATEGY = ", 1)

# 在院校详情弹窗中加入气质描述
old_modal_end = '''<div class="grid grid-cols-2 gap-3 text-sm" id="modal-school-info"></div>'''
new_modal_end = '''<div class="grid grid-cols-2 gap-3 text-sm" id="modal-school-info"></div>
    <div id="modal-school-character" class="mt-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-3 text-sm italic text-gray-600"></div>'''
html = html.replace(old_modal_end, new_modal_end)

# 在openSchoolModal中加入气质显示
old_modal_append = '''document.getElementById('school-modal').classList.remove('hidden');'''
new_modal_append = '''var charEl = document.getElementById('modal-school-character');
  var ch = SCHOOL_CHARACTER[schoolName];
  charEl.textContent = ch ? '📝 '+ch : '';
  document.getElementById('school-modal').classList.remove('hidden');'''
html = html.replace(old_modal_append, new_modal_append)

# ===== 2. 信息分层 — 推荐卡片默认折叠 =====
# 在就业摘要中默认隐藏，加一个"展开详情"按钮更显眼
old_emp_toggle = '''<button onclick="toggleEmpDetail(this)" class="text-blue-500 hover:text-blue-700 ml-auto">展开详情 ▾</button>'''
new_emp_toggle = '''<button onclick="toggleEmpCard(this)" class="text-blue-500 hover:text-blue-700 ml-auto text-xs font-medium">📋 展开全部信息 ▾</button>'''
html = html.replace(old_emp_toggle, new_emp_toggle, 2)  # 替换两处

# 将就业摘要和详情包裹在collapsible中
# 把 "mt-2 bg-gray-50 rounded-lg p-2" 这一段改为可折叠
old_emp_wrapper = '''${item.employment ? `
          <div class="mt-2 bg-gray-50 rounded-lg p-2 text-xs">'''
new_emp_wrapper = '''${item.employment ? `
          <div class="emp-card-detail mt-2 bg-gray-50 rounded-lg p-2 text-xs hidden">'''
html = html.replace(old_emp_wrapper, new_emp_wrapper)

# 在就业摘要前加入精简摘要（始终显示）
old_before_emp = '''<div class="text-xs text-gray-400 mt-1">近3年位次: ${hist}</div>
          ${item.employment ? `'''
new_before_emp = '''<div class="text-xs text-gray-400 mt-1">近3年位次: ${hist}</div>
          ${item.employment ? `<div class="flex flex-wrap gap-2 mt-2 text-xs"><span class="bg-gray-100 rounded px-2 py-0.5">💰 ¥${(item.employment.salary_start/1000).toFixed(0)}K起</span><span class="bg-gray-100 rounded px-2 py-0.5">${(function(){var t=TREND_DATA[item.major_name];return t?t.trend_4yr:item.employment.demand_trend;})()}</span><span class="bg-gray-100 rounded px-2 py-0.5">${(function(){var t=TREND_DATA[item.major_name];return t?t.ai_resilience+' AI抵抗力':'--';})()}</span></div>` : ''}
          ${item.employment ? `'''
html = html.replace(old_before_emp, new_before_emp)

# toggleEmpCard函数
toggle_card_js = '''
function toggleEmpCard(btn) {
  var card = btn.closest('.card');
  var detail = card.querySelector('.emp-card-detail');
  if (detail.classList.contains('hidden')) {
    detail.classList.remove('hidden');
    btn.textContent = '📋 收起详情 ▴';
    if (detail.querySelector('[id^="chart-ind-"]')) renderEmpCharts(detail);
  } else {
    detail.classList.add('hidden');
    btn.textContent = '📋 展开全部信息 ▾';
  }
}
'''
html = html.replace('function toggleEmpDetail', toggle_card_js + '\nfunction toggleEmpDetail')

# ===== 3. 分档冲稳保策略 =====
tier_strategy_js = '''
function getScoreTierAdvice(myRank) {
  if (myRank <= 3000) return {
    tier: '顶配选手',
    advice: '你的选择余地极大。建议：冲5-8个顶尖985的核心专业（清北华五），稳20个985/211王牌专业，其余保底。记住——在这个位次，选专业比选学校更重要。',
    reachMax: 8, matchMin: 25, safetyMin: 63
  };
  if (myRank <= 15000) return {
    tier: '高分选手',
    advice: '985是你的主战场。建议：冲5-10个顶级985，稳30个985/211，保56个。可以大胆冲一冲清北华五的冷门专业。',
    reachMax: 10, matchMin: 30, safetyMin: 56
  };
  if (myRank <= 50000) return {
    tier: '中高分选手',
    advice: '211和省重点是你的核心选择。建议：冲10个985冷门/偏远985，稳35个211，保51个省内重点。不建议冲太多，主战场在稳。',
    reachMax: 10, matchMin: 35, safetyMin: 51
  };
  if (myRank <= 100000) return {
    tier: '中分段选手',
    advice: '省属重点本科是你的主战场。建议：冲5个偏远211/双一流，稳30个省重点，保61个普通本科。选个好专业比选好学校重要得多。',
    reachMax: 5, matchMin: 30, safetyMin: 61
  };
  if (myRank <= 200000) return {
    tier: '中低分段选手',
    advice: '普通公办本科是你的核心范围。建议：冲3个双一流冷门，稳25个公办本科，保68个民办/独立学院。务必确保保底充足，先有学上再选好的。',
    reachMax: 3, matchMin: 25, safetyMin: 68
  };
  if (myRank <= 310000) return {
    tier: '本科线附近',
    advice: '你接近一段线，竞争激烈。建议：冲1-2个最低分公办，稳20个民办本科，保74个确保录取。核心策略：确保有本科上。',
    reachMax: 2, matchMin: 20, safetyMin: 74
  };
  return {
    tier: '一段线附近',
    advice: '你在本科线边缘，首要任务是确保被录取。不建议冲，全填保底。可考虑专科批或3+2对口贯通培养作为备选。',
    reachMax: 0, matchMin: 10, safetyMin: 86
  };
}
'''
html = html.replace('// ==================== 位次换算 ====================', tier_strategy_js + '\n// ==================== 位次换算 ====================')

# 在 rank-display 中展示策略建议
old_rank_end = '''<div class="bg-white rounded-lg px-4 py-2 border">
        <p class="text-xs text-gray-500">📌 ${zone}</p>
      </div>
    </div>`;'''
new_rank_end = '''<div class="bg-white rounded-lg px-4 py-2 border">
        <p class="text-xs text-gray-500">📌 ${zone}</p>
      </div>
    </div>
    <div class="mt-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3 text-sm" id="tier-advice"></div>`;'''
html = html.replace(old_rank_end, new_rank_end)

# 在 renderRank 后填充策略建议
old_render_end2 = '''document.getElementById('rank-display').innerHTML ='''
new_render_end2 = '''var tier = getScoreTierAdvice(data.my_rank.rank);
  var tierAdviceHtml = '<p class="font-medium text-blue-800">🎯 '+tier.tier+'</p><p class="text-xs text-blue-700 mt-1">'+tier.advice+'</p>';
  // 存到state供后续使用
  state.scoreTier = tier;
document.getElementById('rank-display').innerHTML ='''
html = html.replace(old_render_end2, new_render_end2)

# 在renderRank中追加策略
old_rank_inner_end = '''</div>`;'''  # 第一个出现的</div>`; 在renderRank中
# 实际上我们需要在renderRank的HTML字符串末尾追加
html = html.replace('''
    </div>`;''', '''
    </div>
    <div class="mt-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3 text-sm" id="tier-advice"></div>`;''', 1)

# 在renderRank后调用
html = html.replace('''
function renderRank(data) {''', '''
function renderRank(data) {
  var tier = getScoreTierAdvice(data.my_rank.rank);
  state.scoreTier = tier;
  setTimeout(function(){
    var el = document.getElementById('tier-advice');
    if(el) el.innerHTML = '<p class="font-medium text-blue-800">🎯 '+tier.tier+'</p><p class="text-xs text-blue-700 mt-1">'+tier.advice+'</p>';
  },10);
''')

# ===== 4. 冲稳保决策标签 =====
# 在卡片中加入"值得冲"/"不建议冲"
old_strategy_tag = '''<span class="'+tag+'">'+tagLabel+'</span>'''
new_strategy_tag = '''<span class="'+tag+'">'+tagLabel+'</span>
            '+(item.strategy==='reach'||item.strategy==='冲'?(item.probability>=0.15?'<span class="text-xs text-green-600 ml-1">✓值得一冲</span>':'<span class="text-xs text-gray-400 ml-1">·希望不大</span>'):'')+'''
html = html.replace(old_strategy_tag, new_strategy_tag)

# ===== 5. 模块打通 — 兴趣测评结果贯穿推荐 =====
# 在推荐列表中标记"根据你的测评，这个很适合你"
old_card_school_level = '''<span class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">${item.school_level}</span>'''
new_card_school_level = '''<span class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">${item.school_level}</span>
            ${(function(){if(window._quizTopCat && item._prefMatch>=1.0 && window._quizTopCat.some(function(c){return item.major_name.includes(c)||(MAJOR_CATEGORIES[c]||{keywords:[]}).keywords.some(function(k){return item.major_name.includes(k);});})) return '<span class="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium" title=\"根据你的兴趣测评结果\">🧠 适合你</span>'; return '';})()}'''
html = html.replace(old_card_school_level, new_card_school_level)

# 在applyQuizResult中保存quiz top category
old_quiz_apply = '''document.querySelectorAll('#major-pref-selector .subject-chip').forEach(function(b){
    if (g.recommend.includes(b.dataset.cat)) b.classList.add('active');
  });
  updateMajorPrefDisplay();
  document.getElementById('interest-quiz-section').open = false;'''
new_quiz_apply = '''var sorted = Object.entries(quizScores).sort(function(a,b){return b[1]-a[1];});
  window._quizTopCat = sorted.slice(0,3).map(function(x){return x[0];});
  document.querySelectorAll('#major-pref-selector .subject-chip').forEach(function(b){
    if (g.recommend.includes(b.dataset.cat)) b.classList.add('active');
  });
  updateMajorPrefDisplay();
  document.getElementById('interest-quiz-section').open = false;'''
html = html.replace(old_quiz_apply, new_quiz_apply)

# ===== 6. 经济账计算 =====
cost_calc_js = '''
function calculateCost(volunteers) {
  var totalCost = 0; var results = [];
  volunteers.forEach(function(v){
    var tuition = v.tuition || 5000;
    var living = v.school_city === '北京'||v.school_city === '上海'||v.school_city === '深圳' ? 25000 : 18000;
    var yearCost = tuition + living;
    var fourYear = yearCost * 4;
    var empData = v.employment;
    var startSalary = empData ? getSchoolAdjustedSalary(v.school_name, empData.salary_start)*12 : 80000;
    var paybackYrs = (fourYear / startSalary).toFixed(1);
    results.push({name:v.school_name+'·'+v.major_name, fourYear:fourYear, startSalary:Math.round(startSalary), payback:paybackYrs});
    totalCost += fourYear;
  });
  return {results:results, avgCost:volunteers.length?Math.round(totalCost/volunteers.length):0};
}
'''
html = html.replace('// ==================== 位次换算 ====================', cost_calc_js + '\n' + html.split('// ==================== 位次换算 ====================')[1], 1) if 'cost_calc_js' not in html else None

# 在分析面板中加入经济账
old_analysis_panel_start = '''<div id="analysis-panel" class="hidden mt-6 border-t pt-4">'''
new_analysis_panel_start = '''<div id="analysis-panel" class="hidden mt-6 border-t pt-4">
    <div id="cost-analysis" class="mb-4 bg-green-50 rounded-lg p-3 text-sm hidden"></div>'''
html = html.replace(old_analysis_panel_start, new_analysis_panel_start)

# 在 analyzeVolunteer 中调用
old_analyze_call = '''var analysis = analyzeStrategy(state.volunteers, state.myRank.rank);'''
new_analyze_call = '''var analysis = analyzeStrategy(state.volunteers, state.myRank.rank);
  var costData = calculateCost(state.volunteers.slice(0,6));
  var costEl = document.getElementById('cost-analysis');
  if(costEl && costData.results.length>0) {
    costEl.classList.remove('hidden');
    costEl.innerHTML = '<p class="font-medium text-green-800">💰 经济账估算（前6个志愿）</p><p class="text-xs text-green-700 mt-1">四年总花费约 ¥'+(costData.avgCost/10000).toFixed(1)+'万/校 · 毕业首年薪资约 ¥'+costData.results[0].startSalary.toLocaleString()+' · 约需 '+costData.results[0].payback+' 年回本</p><p class="text-xs text-gray-500 mt-1">注：基于学费+城市生活费的粗略估算，仅供参考</p>';
  }'''
html = html.replace(old_analyze_call, new_analyze_call)

# ===== 7. 化解分歧引导 =====
html = html.replace('''
  if (intersection.length === 0 && (studentOnly.length>0 || parentOnly.length>0)) {
    html += '<p class="text-red-600 mt-1">⚠️ 家长和学生没有共同偏好，建议坐下来好好聊聊各自的想法</p>';
  }''', '''
  if (intersection.length === 0 && (studentOnly.length>0 || parentOnly.length>0)) {
    html += '<p class="text-red-600 mt-1">⚠️ 家长和学生没有共同偏好，建议坐下来好好聊聊各自的想法</p>';
    // 中间路线建议
    var allCats = studentOnly.concat(parentOnly);
    if (allCats.indexOf('医学类')>=0 && allCats.indexOf('计算机类')>=0) html += '<p class="text-purple-600 mt-1 text-xs">💡 中间路线：考虑<strong>医学信息学、生物医学工程</strong>等交叉专业，兼顾技术和稳定的需求</p>';
    else if (allCats.indexOf('经管类')>=0 && allCats.indexOf('计算机类')>=0) html += '<p class="text-purple-600 mt-1 text-xs">💡 中间路线：考虑<strong>金融科技、信息管理</strong>等交叉专业</p>';
    else if (allCats.indexOf('师范语言类')>=0 && allCats.indexOf('计算机类')>=0) html += '<p class="text-purple-600 mt-1 text-xs">💡 中间路线：考虑<strong>教育技术学、数字媒体</strong>等交叉专业</p>';
  }''')

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html', 'w') as f:
    f.write(html)

print(f'Done. {len(html)} chars ({len(html.encode())/1024:.0f} KB)')
