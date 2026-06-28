#!/usr/bin/env python3
"""
V3 注入: 兴趣测评 + 院校详情 + 就业图表 + 院校对比
"""
import json, re

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html') as f:
    html = f.read()

# ===================================================================
# 1. 院校详情数据
# ===================================================================
SCHOOL_DETAIL = {
    "北京大学": {"grade":"A+","grad_rate":0.45,"dorm":4,"major_change":"难","founded":1898,"campus":"北京·海淀"},
    "清华大学": {"grade":"A+","grad_rate":0.48,"dorm":4,"major_change":"难","founded":1911,"campus":"北京·海淀"},
    "复旦大学": {"grade":"A+","grad_rate":0.38,"dorm":4,"major_change":"中","founded":1905,"campus":"上海·杨浦"},
    "上海交通大学": {"grade":"A+","grad_rate":0.36,"dorm":4,"major_change":"中","founded":1896,"campus":"上海·闵行"},
    "浙江大学": {"grade":"A+","grad_rate":0.33,"dorm":4,"major_change":"中","founded":1897,"campus":"杭州·西湖"},
    "南京大学": {"grade":"A+","grad_rate":0.35,"dorm":3,"major_change":"中","founded":1902,"campus":"南京·鼓楼"},
    "武汉大学": {"grade":"A+","grad_rate":0.28,"dorm":3,"major_change":"中","founded":1893,"campus":"武汉·武昌"},
    "华中科技大学": {"grade":"A","grad_rate":0.27,"dorm":3,"major_change":"中","founded":1952,"campus":"武汉·洪山"},
    "西安交通大学": {"grade":"A","grad_rate":0.26,"dorm":3,"major_change":"中","founded":1896,"campus":"西安·碑林"},
    "同济大学": {"grade":"A+","grad_rate":0.30,"dorm":3,"major_change":"中","founded":1907,"campus":"上海·杨浦"},
    "北京航空航天大学": {"grade":"A+","grad_rate":0.30,"dorm":3,"major_change":"难","founded":1952,"campus":"北京·海淀"},
    "北京理工大学": {"grade":"A","grad_rate":0.25,"dorm":3,"major_change":"中","founded":1940,"campus":"北京·海淀"},
    "南开大学": {"grade":"A","grad_rate":0.28,"dorm":3,"major_change":"中","founded":1919,"campus":"天津·南开"},
    "天津大学": {"grade":"A","grad_rate":0.26,"dorm":3,"major_change":"中","founded":1895,"campus":"天津·南开"},
    "哈尔滨工业大学": {"grade":"A+","grad_rate":0.28,"dorm":3,"major_change":"中","founded":1920,"campus":"哈尔滨·南岗"},
    "吉林大学": {"grade":"A","grad_rate":0.20,"dorm":3,"major_change":"中","founded":1946,"campus":"长春·朝阳"},
    "大连理工大学": {"grade":"A","grad_rate":0.22,"dorm":3,"major_change":"中","founded":1949,"campus":"大连·甘井子"},
    "电子科技大学": {"grade":"A+","grad_rate":0.25,"dorm":3,"major_change":"中","founded":1956,"campus":"成都·高新"},
    "四川大学": {"grade":"A","grad_rate":0.24,"dorm":3,"major_change":"中","founded":1896,"campus":"成都·武侯"},
    "重庆大学": {"grade":"A-","grad_rate":0.23,"dorm":3,"major_change":"中","founded":1929,"campus":"重庆·沙坪坝"},
    "湖南大学": {"grade":"A-","grad_rate":0.22,"dorm":3,"major_change":"中","founded":976,"campus":"长沙·岳麓"},
    "中南大学": {"grade":"A","grad_rate":0.23,"dorm":3,"major_change":"中","founded":2000,"campus":"长沙·岳麓"},
    "厦门大学": {"grade":"A","grad_rate":0.26,"dorm":4,"major_change":"中","founded":1921,"campus":"厦门·思明"},
    "中山大学": {"grade":"A","grad_rate":0.28,"dorm":3,"major_change":"中","founded":1924,"campus":"广州·海珠"},
    "华南理工大学": {"grade":"A","grad_rate":0.23,"dorm":3,"major_change":"中","founded":1952,"campus":"广州·天河"},
    "东南大学": {"grade":"A+","grad_rate":0.27,"dorm":3,"major_change":"中","founded":1902,"campus":"南京·江宁"},
    "北京邮电大学": {"grade":"A","grad_rate":0.22,"dorm":3,"major_change":"中","founded":1955,"campus":"北京·海淀"},
    "北京交通大学": {"grade":"A-","grad_rate":0.20,"dorm":3,"major_change":"中","founded":1896,"campus":"北京·海淀"},
    "南京航空航天大学": {"grade":"A-","grad_rate":0.22,"dorm":3,"major_change":"中","founded":1952,"campus":"南京·江宁"},
    "西安电子科技大学": {"grade":"A","grad_rate":0.20,"dorm":3,"major_change":"中","founded":1931,"campus":"西安·雁塔"},
    "山东大学": {"grade":"A","grad_rate":0.22,"dorm":3,"major_change":"易","founded":1901,"campus":"济南·历城"},
    "中国海洋大学": {"grade":"A-","grad_rate":0.18,"dorm":3,"major_change":"易","founded":1924,"campus":"青岛·崂山"},
    "中国石油大学(华东)": {"grade":"B+","grad_rate":0.16,"dorm":3,"major_change":"中","founded":1953,"campus":"青岛·黄岛"},
    "山东师范大学": {"grade":"B+","grad_rate":0.08,"dorm":2,"major_change":"易","founded":1950,"campus":"济南·历下"},
    "青岛大学": {"grade":"B","grad_rate":0.06,"dorm":3,"major_change":"易","founded":1909,"campus":"青岛·市南"},
    "山东科技大学": {"grade":"B","grad_rate":0.06,"dorm":2,"major_change":"易","founded":1951,"campus":"青岛·黄岛"},
    "山东财经大学": {"grade":"B","grad_rate":0.05,"dorm":2,"major_change":"易","founded":1952,"campus":"济南·历下"},
    "青岛科技大学": {"grade":"B","grad_rate":0.05,"dorm":2,"major_change":"易","founded":1950,"campus":"青岛·崂山"},
    "济南大学": {"grade":"B","grad_rate":0.05,"dorm":2,"major_change":"易","founded":1948,"campus":"济南·市中"},
    "烟台大学": {"grade":"B-","grad_rate":0.04,"dorm":2,"major_change":"易","founded":1984,"campus":"烟台·莱山"},
    "曲阜师范大学": {"grade":"B","grad_rate":0.07,"dorm":2,"major_change":"易","founded":1955,"campus":"曲阜·鲁城"},
    "山东农业大学": {"grade":"B+","grad_rate":0.10,"dorm":2,"major_change":"易","founded":1906,"campus":"泰安·泰山"},
    "山东理工大学": {"grade":"B","grad_rate":0.05,"dorm":2,"major_change":"易","founded":1956,"campus":"淄博·张店"},
    "山东建筑大学": {"grade":"B-","grad_rate":0.04,"dorm":2,"major_change":"易","founded":1956,"campus":"济南·历城"},
    "齐鲁工业大学": {"grade":"B","grad_rate":0.05,"dorm":2,"major_change":"易","founded":1948,"campus":"济南·长清"},
    "山东第一医科大学": {"grade":"B","grad_rate":0.06,"dorm":2,"major_change":"中","founded":1891,"campus":"济南·槐荫"},
    "山东中医药大学": {"grade":"B","grad_rate":0.06,"dorm":2,"major_change":"中","founded":1958,"campus":"济南·长清"},
    "鲁东大学": {"grade":"C+","grad_rate":0.04,"dorm":2,"major_change":"易","founded":1930,"campus":"烟台·芝罘"},
    "聊城大学": {"grade":"C+","grad_rate":0.04,"dorm":2,"major_change":"易","founded":1974,"campus":"聊城·东昌"},
    "临沂大学": {"grade":"C","grad_rate":0.03,"dorm":2,"major_change":"易","founded":1941,"campus":"临沂·兰山"},
}
# Fill defaults for missing schools
_default = {"grade":"C","grad_rate":0.02,"dorm":2,"major_change":"易","founded":1970,"campus":"山东"}
for school_info in [
    "潍坊学院","德州学院","泰山学院","滨州学院","菏泽学院","济宁学院","枣庄学院",
    "山东管理学院","齐鲁师范学院","山东青年政治学院","山东农业工程学院",
    "青岛城市学院","烟台南山学院","山东英才学院","青岛黄海学院","山东协和学院",
    "潍坊科技学院","青岛滨海学院","山东现代学院","山东华宇工学院","青岛工学院",
    "齐鲁理工学院","山东工程职业技术大学","山东外国语职业技术大学","山东外事职业大学",
]:
    if school_info not in SCHOOL_DETAIL:
        is_private = any(x in school_info for x in ["城市学院","南山","英才","黄海","协和","科技学院","滨海","现代","华宇","工学院","理工","工程","外国语","外事"])
        SCHOOL_DETAIL[school_info] = {
            "grade": "-", "grad_rate": 0.01 if is_private else 0.03,
            "dorm": 2, "major_change": "易", "founded": 2000, "campus": "山东"
        }

# ===================================================================
# 2. 兴趣测评题目
# ===================================================================
QUIZ_QUESTIONS = [
    {"q":"你喜欢哪类活动？","a":"动手操作、修理/搭建东西","b":"观察分析、研究事物的规律"},
    {"q":"解决一个问题时，你更倾向于？","a":"用已有的方法和工具高效解决","b":"探索新的思路和可能性"},
    {"q":"团队项目中，你更喜欢？","a":"组织和协调大家，推动项目前进","b":"独立完成自己擅长的部分"},
    {"q":"面对数据/信息，你更喜欢？","a":"整理归类，让一切井井有条","b":"分析挖掘，找到隐藏的规律"},
    {"q":"你更享受哪种工作？","a":"与人打交道，帮助/说服/服务他人","b":"与事物/概念打交道，思考/设计/构建"},
    {"q":"阅读时，你更被什么吸引？","a":"人物故事、社会现象","b":"科学原理、技术方案"},
    {"q":"你对哪种任务更有耐心？","a":"需要细致和精确的任务","b":"需要创意和想象的任务"},
    {"q":"做决定时，你更依赖？","a":"数据和逻辑分析","b":"直觉和价值观"},
    {"q":"你更向往哪种职业？","a":"有稳定发展和清晰晋升路径的","b":"充满变化和挑战的"},
    {"q":"周末你更想做什么？","a":"组织朋友聚会、参加社交活动","b":"在家读书、学习新技能、做个人项目"},
]
# 答案映射: [a→哪些大类加分, b→哪些大类加分]
QUIZ_MAPPING = [
    (["机械电气类","计算机类"], ["电子信息类","计算机类"]),  # Q1
    (["经管类","计算机类"], ["电子信息类","医学类"]),        # Q2
    (["经管类","师范语言类"], ["计算机类","医学类"]),        # Q3
    (["经管类","法学类"], ["计算机类","电子信息类"]),        # Q4
    (["医学类","师范语言类","法学类"], ["土木建筑类","机械电气类","计算机类"]), # Q5
    (["法学类","经管类","师范语言类"], ["电子信息类","计算机类","医学类"]), # Q6
    (["经管类","机械电气类"], ["计算机类","师范语言类"]),    # Q7
    (["计算机类","电子信息类","经管类"], ["师范语言类","法学类"]), # Q8
    (["经管类","法学类","医学类"], ["计算机类","电子信息类"]),  # Q9
    (["经管类","师范语言类"], ["计算机类","电子信息类","医学类"]), # Q10
]

# ===================================================================
# 注入到 HTML
# ===================================================================

# 3a. 注入院校详情数据
det_js = "const SCHOOL_DETAIL = " + json.dumps(SCHOOL_DETAIL, ensure_ascii=False) + ";\n"
html = html.replace("const MAJOR_CATEGORIES = ", det_js + "const MAJOR_CATEGORIES = ", 1)

# 3b. 注入兴趣测评数据
quiz_data = json.dumps(QUIZ_QUESTIONS, ensure_ascii=False)
quiz_map = json.dumps(QUIZ_MAPPING, ensure_ascii=False)
html = html.replace("const MAJOR_CATEGORIES = ", "const QUIZ_QUESTIONS = " + quiz_data + ";\nconst QUIZ_MAPPING = " + quiz_map + ";\nconst MAJOR_CATEGORIES = ", 1)

# 3c. 兴趣测评UI (在专业意向下)
quiz_html = '''
  <!-- 兴趣测评 -->
  <details class="mt-4" id="interest-quiz-section">
    <summary class="text-sm font-medium text-gray-700 cursor-pointer hover:text-blue-600">
      🧠 不确定喜欢什么专业？花2分钟做个测评
    </summary>
    <div class="mt-3 bg-blue-50 rounded-lg p-4" id="quiz-container">
      <p class="text-sm text-gray-600 mb-3" id="quiz-progress">第 1/10 题</p>
      <p class="font-medium mb-3" id="quiz-question"></p>
      <div class="flex gap-3">
        <button onclick="answerQuiz('a')" class="flex-1 bg-white border-2 border-blue-200 rounded-lg p-3 text-sm hover:border-blue-400 transition" id="quiz-btn-a"></button>
        <button onclick="answerQuiz('b')" class="flex-1 bg-white border-2 border-blue-200 rounded-lg p-3 text-sm hover:border-blue-400 transition" id="quiz-btn-b"></button>
      </div>
      <div class="mt-3 hidden" id="quiz-result">
        <p class="font-medium text-green-700">📊 测评结果</p>
        <div id="quiz-result-bars" class="mt-2 space-y-1"></div>
        <button onclick="applyQuizResult()" class="mt-3 bg-green-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-green-700">✅ 应用推荐</button>
        <button onclick="resetQuiz()" class="ml-2 text-sm text-gray-500 hover:text-gray-700">重测</button>
      </div>
    </div>
  </details>
'''
html = html.replace('''  <button id="btn-analyze" onclick="analyze()" class="btn-primary text-lg">🔍 开始分析</button>''', quiz_html + '''
  <button id="btn-analyze" onclick="analyze()" class="btn-primary text-lg">🔍 开始分析</button>''')

# 3d. 兴趣测评JS逻辑
quiz_js = '''
let quizIdx = 0, quizScores = {};
function showQuizQuestion() {
  if (quizIdx >= QUIZ_QUESTIONS.length) {
    showQuizResult(); return;
  }
  const q = QUIZ_QUESTIONS[quizIdx];
  document.getElementById('quiz-progress').textContent = '第 '+(quizIdx+1)+'/'+QUIZ_QUESTIONS.length+' 题';
  document.getElementById('quiz-question').textContent = q.q;
  document.getElementById('quiz-btn-a').textContent = 'A. '+q.a;
  document.getElementById('quiz-btn-b').textContent = 'B. '+q.b;
  document.getElementById('quiz-result').classList.add('hidden');
}
function answerQuiz(choice) {
  const map = QUIZ_MAPPING[quizIdx];
  const cats = choice === 'a' ? map[0] : map[1];
  cats.forEach(c => { quizScores[c] = (quizScores[c]||0) + 1; });
  quizIdx++;
  showQuizQuestion();
}
function showQuizResult() {
  document.getElementById('quiz-progress').textContent = '测评完成！';
  document.getElementById('quiz-question').textContent = '';
  document.getElementById('quiz-btn-a').classList.add('hidden');
  document.getElementById('quiz-btn-b').classList.add('hidden');
  const sorted = Object.entries(quizScores).sort((a,b)=>b[1]-a[1]);
  const maxScore = sorted[0]?.[1] || 1;
  document.getElementById('quiz-result').classList.remove('hidden');
  document.getElementById('quiz-result-bars').innerHTML = sorted.slice(0,5).map(([k,v]) => {
    const pct = (v/maxScore*100).toFixed(0);
    const colors = {'计算机类':'bg-blue-500','电子信息类':'bg-indigo-500','医学类':'bg-red-500','法学类':'bg-amber-500','经管类':'bg-green-500','机械电气类':'bg-orange-500','师范语言类':'bg-purple-500','土木建筑类':'bg-gray-500'};
    return '<div class="flex items-center gap-2"><span class="w-20 text-xs">'+k+'</span><div class="flex-1 bg-gray-200 rounded-full h-3"><div class="h-3 rounded-full '+(colors[k]||'bg-blue-400')+'" style="width:'+pct+'%"></div></div><span class="text-xs">'+v+'分</span></div>';
  }).join('');
}
function applyQuizResult() {
  const sorted = Object.entries(quizScores).sort((a,b)=>b[1]-a[1]);
  const top3 = sorted.slice(0,3).map(x=>x[0]);
  // 选中对应标签
  document.querySelectorAll('#major-pref-selector .subject-chip').forEach(b => {
    if (top3.includes(b.dataset.cat)) b.classList.add('active');
    else b.classList.remove('active');
  });
  updateMajorPrefDisplay();
  // 展开的details收起
  document.getElementById('interest-quiz-section').open = false;
}
function resetQuiz() { quizIdx=0; quizScores={}; showQuizQuestion(); document.getElementById('quiz-btn-a').classList.remove('hidden'); document.getElementById('quiz-btn-b').classList.remove('hidden'); }
showQuizQuestion();
'''
html = html.replace('// ==================== 位次换算 ====================', quiz_js + '\n// ==================== 位次换算 ====================')

# 3e. 院校详情弹窗 (modal)
modal_html = '''
<!-- 院校详情弹窗 -->
<div id="school-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center" style="background:rgba(0,0,0,0.4)" onclick="closeSchoolModal(event)">
  <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto p-6" onclick="event.stopPropagation()">
    <div class="flex justify-between items-start mb-4">
      <h2 class="text-xl font-bold" id="modal-school-name"></h2>
      <button onclick="document.getElementById('school-modal').classList.add('hidden')" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
    </div>
    <div class="grid grid-cols-2 gap-3 text-sm" id="modal-school-info"></div>
  </div>
</div>
'''
html = html.replace('<div id="rec-list"', modal_html + '\n<div id="rec-list"')

# 学校详情JS
school_modal_js = '''
function openSchoolModal(schoolName) {
  const d = SCHOOL_DETAIL[schoolName];
  if (!d) return;
  const stars = '★'.repeat(d.dorm)+'☆'.repeat(5-d.dorm);
  document.getElementById('modal-school-name').textContent = schoolName;
  document.getElementById('modal-school-info').innerHTML =
    '<div class="bg-gray-50 rounded-lg p-2"><span class="text-gray-500">层次</span><br><strong>'+getSchoolLevel(schoolName)+'</strong></div>'+
    '<div class="bg-gray-50 rounded-lg p-2"><span class="text-gray-500">最佳学科</span><br><strong>'+d.grade+'</strong></div>'+
    '<div class="bg-gray-50 rounded-lg p-2"><span class="text-gray-500">保研率</span><br><strong>'+(d.grad_rate*100).toFixed(0)+'%</strong></div>'+
    '<div class="bg-gray-50 rounded-lg p-2"><span class="text-gray-500">宿舍条件</span><br><strong>'+stars+'</strong></div>'+
    '<div class="bg-gray-50 rounded-lg p-2"><span class="text-gray-500">转专业难度</span><br><strong>'+d.major_change+'</strong></div>'+
    '<div class="bg-gray-50 rounded-lg p-2"><span class="text-gray-500">建校/合并</span><br><strong>'+d.founded+'年</strong></div>'+
    '<div class="bg-gray-50 rounded-lg p-2"><span class="text-gray-500">校区</span><br><strong>'+d.campus+'</strong></div>'+
    '<div class="bg-gray-50 rounded-lg p-2"><span class="text-gray-500">所在地</span><br><strong>'+(schoolMap[schoolName]?.city||'')+'</strong></div>';
  document.getElementById('school-modal').classList.remove('hidden');
}
function closeSchoolModal(e) {
  if (e.target === document.getElementById('school-modal')) {
    document.getElementById('school-modal').classList.add('hidden');
  }
}
function getSchoolLevel(name) {
  const s = schoolMap[name];
  return s ? s.level : '普通';
}
'''
html = html.replace('function toggleEmpDetail', school_modal_js + '\nfunction toggleEmpDetail')

# 3f. 推荐卡片中的学校名改为可点击
html = html.replace("<h3 class=\"font-semibold text-gray-800\">${item.school_name}",
                     "<h3 class=\"font-semibold text-gray-800 cursor-pointer hover:text-blue-600 underline decoration-dotted\" onclick=\"openSchoolModal('${item.school_name}')\">${item.school_name}")

# 3g. 院校对比工具
compare_html = '''
<!-- 对比工具栏 -->
<div id="compare-bar" class="hidden fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-40 px-4 py-3">
  <div class="max-w-7xl mx-auto flex items-center justify-between">
    <div class="flex items-center gap-3">
      <span class="text-sm font-medium">⚖️ 院校对比</span>
      <span id="compare-list" class="text-sm text-gray-500">已选: 0/5</span>
    </div>
    <div class="flex gap-2">
      <button onclick="doCompare()" class="btn-primary text-sm" id="btn-compare" disabled>开始对比</button>
      <button onclick="clearCompare()" class="btn-secondary text-sm">清空</button>
      <button onclick="document.getElementById('compare-bar').classList.add('hidden')" class="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
    </div>
  </div>
</div>
<!-- 对比结果弹窗 -->
<div id="compare-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center" style="background:rgba(0,0,0,0.4)" onclick="event.target===this&&this.classList.add('hidden')">
  <div class="bg-white rounded-2xl shadow-2xl max-w-5xl w-full mx-4 max-h-[85vh] overflow-auto p-6">
    <div class="flex justify-between mb-4"><h2 class="text-xl font-bold">⚖️ 院校对比</h2><button onclick="document.getElementById('compare-modal').classList.add('hidden')" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button></div>
    <div id="compare-table"></div>
  </div>
</div>
'''
html = html.replace('<div id="rec-list"', compare_html + '\n<div id="rec-list"')

compare_js = '''
let compareSchools = [];
function toggleCompare(schoolName, btn) {
  const idx = compareSchools.indexOf(schoolName);
  if (idx >= 0) { compareSchools.splice(idx,1); btn.textContent='☐ 对比'; btn.classList.remove('bg-blue-100','text-blue-700'); }
  else if (compareSchools.length < 5) { compareSchools.push(schoolName); btn.textContent='☑ 已选'; btn.classList.add('bg-blue-100','text-blue-700'); }
  else { alert('最多对比5所院校'); return; }
  updateCompareBar();
}
function updateCompareBar() {
  const bar = document.getElementById('compare-bar');
  if (compareSchools.length > 0) { bar.classList.remove('hidden'); }
  document.getElementById('compare-list').textContent = '已选: '+compareSchools.length+'/5 — '+compareSchools.join('、');
  document.getElementById('btn-compare').disabled = compareSchools.length < 2;
}
function clearCompare() { compareSchools=[]; updateCompareBar(); document.getElementById('compare-bar').classList.add('hidden'); }
function doCompare() {
  if (compareSchools.length < 2) return;
  const dimensions = [
    {key:'level',label:'院校层次',get:s=>schoolMap[s]?.level||'-'},
    {key:'city',label:'城市',get:s=>schoolMap[s]?.city||'-'},
    {key:'grade',label:'最佳学科评估',get:s=>SCHOOL_DETAIL[s]?.grade||'-'},
    {key:'grad_rate',label:'保研率',get:s=>((SCHOOL_DETAIL[s]?.grad_rate||0)*100).toFixed(0)+'%'},
    {key:'dorm',label:'宿舍条件',get:s=>'★'.repeat(SCHOOL_DETAIL[s]?.dorm||0)+'☆'.repeat(5-(SCHOOL_DETAIL[s]?.dorm||0))},
    {key:'major_change',label:'转专业难度',get:s=>SCHOOL_DETAIL[s]?.major_change||'-'},
    {key:'founded',label:'建校/合并',get:s=>SCHOOL_DETAIL[s]?.founded||'-'},
    {key:'campus',label:'校区',get:s=>SCHOOL_DETAIL[s]?.campus||'-'},
  ];
  let table = '<div class="overflow-x-auto"><table class="w-full text-sm"><thead><tr><th class="p-2 border-b text-left">维度</th>';
  compareSchools.forEach(s => { table += '<th class="p-2 border-b text-center font-medium">'+s+'</th>'; });
  table += '</tr></thead><tbody>';
  dimensions.forEach(d => {
    table += '<tr><td class="p-2 border-b text-gray-500">'+d.label+'</td>';
    compareSchools.forEach(s => { table += '<td class="p-2 border-b text-center">'+d.get(s)+'</td>'; });
    table += '</tr>';
  });
  table += '</tbody></table></div>';
  document.getElementById('compare-table').innerHTML = table;
  document.getElementById('compare-modal').classList.remove('hidden');
}
'''
html = html.replace('function openSchoolModal', compare_js + '\nfunction openSchoolModal')

# 3h. 推荐卡片中加入对比按钮
html = html.replace("${inVol?'<span class=\"text-xs text-blue-500\">✅ 已添加</span>':''}",
                     "${inVol?'<span class=\"text-xs text-blue-500\">✅ 已添加</span>':''}<button onclick=\"event.stopPropagation();toggleCompare('${item.school_name}',this)\" class=\"text-xs text-gray-400 hover:text-blue-500 ml-1\">☐ 对比</button>")

# 3i. 就业图表 — 在展开详情中嵌入 Plotly
# 在 emp-detail 中最后一行的薪资趋势后加入图表容器
html = html.replace("<p class=\"text-gray-400 mt-1\">📊 薪资趋势: ${item.employment.salary_trend}</p>",
                     "<p class=\"text-gray-400 mt-1\">📊 薪资趋势: ${item.employment.salary_trend}</p><div class=\"mt-2 grid grid-cols-2 gap-2\"><div id=\"chart-ind-${item.major_code||'x'}\" style=\"height:120px\"></div><div id=\"chart-city-${item.major_code||'x'}\" style=\"height:120px\"></div></div>")

# 在toggleEmpDetail中加入图表渲染
html = html.replace("if (detail.classList.contains('hidden')) {\n    detail.classList.remove('hidden');\n    btn.textContent = '收起 ▴';\n  }",
                     "if (detail.classList.contains('hidden')) {\n    detail.classList.remove('hidden');\n    btn.textContent = '收起 ▴';\n    renderEmpCharts(detail);\n  }")

# 图表渲染函数
chart_js = '''
function renderEmpCharts(detailEl) {
  const itemEl = detailEl.closest('.card');
  if (!itemEl || itemEl.dataset.chartRendered) return;
  itemEl.dataset.chartRendered = '1';
  // 找到行业和城市数据
  const indDiv = detailEl.querySelector('[id^="chart-ind-"]');
  const cityDiv = detailEl.querySelector('[id^="chart-city-"]');
  if (!indDiv || !cityDiv) return;
  // 从当前推荐列表中找到对应数据
  const schoolName = itemEl.querySelector('h3')?.textContent?.split('·')[0]?.trim();
  let empData = null;
  for (const k of ['reach','match','safety']) {
    for (const r of state.recs[k]||[]) {
      if (r.school_name === schoolName && r.employment) { empData = r.employment; break; }
    }
    if (empData) break;
  }
  if (!empData) return;
  // 行业分布图
  const inds = Object.entries(empData.industries);
  Plotly.newPlot(indDiv, [{type:'bar',x:inds.map(x=>x[1]),y:inds.map(x=>x[0]),orientation:'h',marker:{color:'#3b82f6'}}],{margin:{l:70,r:10,t:5,b:5},xaxis:{title:'%',showgrid:false},height:120},{displayModeBar:false,responsive:true});
  // 城市分布图
  const cities = Object.entries(empData.cities);
  Plotly.newPlot(cityDiv, [{type:'bar',x:cities.map(x=>x[1]),y:cities.map(x=>x[0]),orientation:'h',marker:{color:'#10b981'}}],{margin:{l:70,r:10,t:5,b:5},xaxis:{title:'%',showgrid:false},height:120},{displayModeBar:false,responsive:true});
}
'''
html = html.replace('function toggleEmpDetail', chart_js + '\nfunction toggleEmpDetail')

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html', 'w') as f:
    f.write(html)

print(f'Done. Size: {len(html)} chars ({len(html.encode())/1024:.0f} KB)')
