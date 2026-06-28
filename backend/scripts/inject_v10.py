#!/usr/bin/env python3
"""V10: P2 — 家长协作 + 学校就业修正 + 退路信息"""
import json, re

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html') as f:
    html = f.read()

# ===== 1. 退路信息 =====
EXIT_STRATEGY = {
    "计算机科学与技术": {"cross_major":["软件工程","人工智能","数据科学","电子工程"],"second_degree":["金融科技","管理信息系统"],"note":"转行最容易的专业之一，几乎所有理工科和部分商科都可以跨"},
    "软件工程": {"cross_major":["计算机科学","人工智能","信息安全"],"second_degree":["产品设计","数字媒体"],"note":"和计算机类似，转行面广"},
    "通信工程": {"cross_major":["电子工程","计算机科学","自动化"],"second_degree":["物联网工程"],"note":"可转电子/计算机方向，硬件转软件比较常见"},
    "临床医学": {"cross_major":["基础医学","公共卫生","药学"],"second_degree":["医院管理"],"note":"转专业较难，医学培养体系封闭。不喜欢临床可考虑医药企业/医院管理"},
    "口腔医学": {"cross_major":["临床医学（较难）"],"second_degree":["医疗管理"],"note":"口腔比临床灵活，可开诊所创业"},
    "法学": {"cross_major":["公共管理","政治学","社会学"],"second_degree":["会计学","金融学"],"note":"法考是关键，考不过也可以走企业法务/合规方向"},
    "经济学": {"cross_major":["金融学","统计学","工商管理"],"second_degree":["数据科学"],"note":"万金油专业，考研可转金融/管理/统计多个方向"},
    "会计学": {"cross_major":["财务管理","审计学","金融学"],"second_degree":["法学（税法方向）"],"note":"考CPA是核心，转金融/税务都可以"},
    "机械工程": {"cross_major":["车辆工程","自动化","工业设计"],"second_degree":["工商管理"],"note":"传统工科，可转智能制造/机器人方向提升"},
    "车辆工程": {"cross_major":["机械工程","自动化","能源动力"],"second_degree":["工业设计"],"note":"新能源车风口，转自动驾驶/电池方向有前景"},
    "土木工程": {"cross_major":["工程管理","建筑学","城市规划"],"second_degree":["工程造价"],"note":"⚠️ 行业下行，建议尽早考虑跨考/转行"},
    "电气工程及其自动化": {"cross_major":["自动化","能源动力","电子工程"],"second_degree":["计算机科学"],"note":"国网是主出路，也可转新能源/储能方向"},
    "自动化": {"cross_major":["计算机科学","电子工程","机械工程"],"second_degree":["人工智能"],"note":"交叉性强，转行面最广的工科之一"},
    "英语": {"cross_major":["翻译","国际关系","新闻传播"],"second_degree":["法学","国际贸易"],"note":"⚠️ 建议必须叠加第二技能，纯英语竞争力有限"},
    "数学与应用数学": {"cross_major":["统计学","计算机科学","金融工程","数据科学"],"second_degree":["经济学"],"note":"转行万能跳板，数学底子好什么都能转"},
    "社会工作": {"cross_major":["社会学","公共管理","心理学"],"second_degree":["法学"],"note":"考公/考编有专门通道，也可走公益行业"},
    "信息管理与信息系统": {"cross_major":["计算机科学","工商管理","数据科学"],"second_degree":["电子商务"],"note":"交叉学科，可转IT产品经理或数据分析"},
}

# ===== 注入数据 =====
exit_js = "const EXIT_STRATEGY = " + json.dumps(EXIT_STRATEGY, ensure_ascii=False) + ";"
html = html.replace("const MAJOR_ONELINERS = ", exit_js + "\nconst MAJOR_ONELINERS = ", 1)

# ===== 2. 学校就业修正系数 =====
# 在薪资展示时应用修正
# 在决策建议和卡片中加入"本校修正后起薪"
school_salary_fix_js = '''
function getSchoolAdjustedSalary(schoolName, baseSalary) {
  var level = (schoolMap[schoolName]||{}).level;
  if (level === '985') return Math.round(baseSalary * 1.25);
  if (level === '211') return Math.round(baseSalary * 1.12);
  if (level === '双一流') return Math.round(baseSalary * 1.05);
  return Math.round(baseSalary * 0.90); // 普通院校
}
'''
html = html.replace('// ==================== 位次换算 ====================', school_salary_fix_js + '\n// ==================== 位次换算 ====================')

# ===== 3. 就业卡片中显示修正后薪资 =====
# 在"应届起薪"后面加上修正
old_salary_display = '''<span>💰 应届起薪: <strong>¥${(item.employment.salary_start/1000).toFixed(0)}K</strong></span>'''
new_salary_display = '''<span>💰 应届起薪: <strong>¥${(item.employment.salary_start/1000).toFixed(0)}K</strong></span>
              <span class="text-xs text-gray-400">(该校修正: <strong>¥${(getSchoolAdjustedSalary(item.school_name,item.employment.salary_start)/1000).toFixed(0)}K</strong>)</span>'''
html = html.replace(old_salary_display, new_salary_display)

# ===== 4. 就业详情中加入退路信息 =====
old_emp_end = '''<p class="text-gray-400 mt-1">📊 薪资趋势: ${item.employment.salary_trend}</p>'''
new_emp_end = '''<p class="text-gray-400 mt-1">📊 薪资趋势: ${item.employment.salary_trend}</p>
            ${(function(){var es=EXIT_STRATEGY[item.major_name];if(!es)return'';return'<div class=\"mt-2 bg-purple-50 rounded-lg p-2 text-xs\"><p class=\"font-medium text-purple-800\">🔄 如果不喜欢这个专业怎么办</p><p class=\"text-gray-700 mt-1\">📖 考研可跨: '+es.cross_major.join(' · ')+'</p><p class=\"text-gray-700\">🎓 第二学位: '+es.second_degree.join(' · ')+'</p><p class=\"text-gray-500 mt-1\">💬 '+es.note+'</p><p class=\"text-gray-400 mt-1\">🔑 本校转专业难度: <strong>'+(SCHOOL_DETAIL[item.school_name]?SCHOOL_DETAIL[item.school_name].major_change:'-')+'</strong></p></div>';})()}'''
html = html.replace(old_emp_end, new_emp_end)

# ===== 5. 家长协作模式 =====
parent_html = '''
  <!-- 家长协作模式 -->
  <div class="mb-4">
    <label class="inline-flex items-center gap-2 cursor-pointer" onclick="toggleParentMode()">
      <input type="checkbox" id="parent-mode-toggle" class="w-4 h-4 rounded accent-purple-600">
      <span class="text-sm font-medium text-gray-700">👨‍👩‍👧 开启家长协作模式</span>
    </label>
    <span class="text-xs text-gray-400 ml-2">家长和孩子分别标注偏好，系统对比分析</span>
  </div>
  <!-- 家长偏好（默认隐藏）-->
  <div id="parent-prefs" class="hidden mb-4 bg-purple-50 rounded-lg p-4 border border-purple-200">
    <p class="text-sm font-medium text-purple-800 mb-2">🧑‍🤝‍🧑 家长的偏好（请爸爸/妈妈来选择）</p>
    <div class="flex flex-wrap gap-2" id="parent-major-selector"></div>
    <p class="text-xs text-gray-400 mt-1">家长已选: <span id="parent-pref-display" class="text-purple-600 font-medium">未选择</span></p>
  </div>
  <!-- 对比结果 -->
  <div id="parent-compare-result" class="hidden mb-4 bg-green-50 rounded-lg p-4 border border-green-200 text-sm">
    <p class="font-medium text-green-800 mb-2">🤝 家长与学生的偏好对比</p>
    <div id="parent-compare-content"></div>
  </div>
'''

html = html.replace('<div class="mb-6"><label class="block text-sm font-medium text-gray-700 mb-2">🎯 专业意向', parent_html + '\n<div class="mb-6"><label class="block text-sm font-medium text-gray-700 mb-2">🎯 专业意向')

# 家长模式JS
parent_js = '''
let parentMode = false;
let parentPrefs = [];

function toggleParentMode() {
  parentMode = document.getElementById('parent-mode-toggle').checked;
  var panel = document.getElementById('parent-prefs');
  var result = document.getElementById('parent-compare-result');
  if (parentMode) {
    panel.classList.remove('hidden');
    if (!document.getElementById('parent-major-selector').hasChildNodes()) initParentPrefs();
  } else {
    panel.classList.add('hidden');
    result.classList.add('hidden');
  }
}

function initParentPrefs() {
  var cats = [
    {key:'计算机类',label:'💻 计算机类'},
    {key:'电子信息类',label:'📡 电子信息类'},
    {key:'医学类',label:'🩺 医学类'},
    {key:'法学类',label:'⚖️ 法学类'},
    {key:'经管类',label:'💰 经管类'},
    {key:'机械电气类',label:'🔧 机械电气类'},
    {key:'师范语言类',label:'📚 师范语言类'},
    {key:'土木建筑类',label:'🏗 土木建筑类'},
  ];
  var sel = document.getElementById('parent-major-selector');
  cats.forEach(function(c){
    var btn = document.createElement('button');
    btn.className = 'subject-chip';
    btn.textContent = c.label; btn.dataset.cat = c.key;
    btn.onclick = function(){
      if (parentPrefs.includes(c.key)) {
        parentPrefs = parentPrefs.filter(function(x){return x!==c.key;});
        btn.classList.remove('active');
        btn.style.borderColor = '#e5e7eb'; btn.style.background = '#fff'; btn.style.color = '#6b7280';
      } else {
        parentPrefs.push(c.key);
        btn.classList.add('active');
        btn.style.borderColor = '#9333ea'; btn.style.background = '#faf5ff'; btn.style.color = '#9333ea';
      }
      updateParentDisplay();
      updateCompareResult();
    };
    sel.appendChild(btn);
  });
}

function updateParentDisplay() {
  document.getElementById('parent-pref-display').textContent = parentPrefs.length ? parentPrefs.join('、') : '未选择';
}

function updateCompareResult() {
  var result = document.getElementById('parent-compare-result');
  if (!parentPrefs.length && !state.preferredMajors.length) { result.classList.add('hidden'); return; }
  result.classList.remove('hidden');
  var student = state.preferredMajors || [];
  var intersection = student.filter(function(x){return parentPrefs.includes(x);});
  var studentOnly = student.filter(function(x){return !parentPrefs.includes(x);});
  var parentOnly = parentPrefs.filter(function(x){return !student.includes(x);});

  var html = '';
  if (intersection.length > 0) {
    html += '<p class="text-green-700">✅ 共同偏好：<strong>'+intersection.join('、')+'</strong> — 优先考虑这些方向！</p>';
  }
  if (studentOnly.length > 0) {
    html += '<p class="text-blue-600 mt-1">🙋 学生偏好（家长未选）：<strong>'+studentOnly.join('、')+'</strong> — 建议沟通</p>';
  }
  if (parentOnly.length > 0) {
    html += '<p class="text-purple-600 mt-1">🧑 家长偏好（学生未选）：<strong>'+parentOnly.join('、')+'</strong> — 建议沟通</p>';
  }
  if (intersection.length === 0 && (studentOnly.length>0 || parentOnly.length>0)) {
    html += '<p class="text-red-600 mt-1">⚠️ 家长和学生没有共同偏好，建议坐下来好好聊聊各自的想法</p>';
  }
  if (!student.length && !parentPrefs.length) {
    html += '<p class="text-gray-500">双方都还没有选择偏好</p>';
  }
  document.getElementById('parent-compare-content').innerHTML = html;
}

// 在学生选标签时也触发对比更新
var origUpdateMajorPref = updateMajorPrefDisplay;
updateMajorPrefDisplay = function() {
  origUpdateMajorPref();
  if (parentMode) updateCompareResult();
};
'''
html = html.replace('// ==================== 选科UI ====================', parent_js + '\n// ==================== 选科UI ====================')

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html', 'w') as f:
    f.write(html)

print(f'Done. {len(html)} chars ({len(html.encode())/1024:.0f} KB)')
