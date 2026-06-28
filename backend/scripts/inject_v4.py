#!/usr/bin/env python3
"""V4 注入: 人生目标选专业顾问板块 (9个目标)"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, 'goals.json')) as f:
    GOALS = json.load(f)

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html') as f:
    html = f.read()

# 目标卡片HTML
cards_html = ""
for g in GOALS:
    cards_html += '''
      <div class="goal-card bg-white rounded-xl border-2 border-gray-200 hover:border-blue-300 hover:shadow-md transition-all p-3 cursor-pointer" onclick="openGoal(\'''' + g['id'] + '''\')" id="goal-card-''' + g['id'] + '''">
        <div class="text-xl mb-1">''' + g['icon'] + '''</div>
        <div class="font-semibold text-gray-800 text-sm">''' + g['title'] + '''</div>
        <div class="text-xs text-gray-400 mt-0.5">''' + g['short'] + '''</div>
      </div>'''

advisor_section = '''<!-- 选专业顾问板块 -->
<section id="advisor-section" class="card p-6 mb-6 animate-in bg-gradient-to-b from-blue-50/50 to-white">
  <div class="flex items-start justify-between mb-2">
    <div>
      <h2 class="text-xl font-bold">🤔 选专业之前，先想清楚：你更想要什么样的未来？</h2>
      <p class="text-gray-500 text-sm mt-1">每个人18岁时做的选择，会影响此后几十年的人生轨迹。<br>没有标准答案，但有些路确实更适合某些目标。点击你关心的选项，看看客观数据和过来人的分析。</p>
    </div>
  </div>

  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 mt-4">
    ''' + cards_html + '''
  </div>

  <div id="goal-detail" class="hidden mt-4 bg-white rounded-xl border-2 border-blue-200 p-5">
    <div class="flex justify-between items-start mb-3">
      <h3 class="text-lg font-bold" id="goal-detail-title"></h3>
      <button onclick="closeGoal()" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
    </div>
    <div id="goal-detail-content" class="text-sm text-gray-700 space-y-2"></div>
    <div class="mt-4 flex gap-2">
      <button onclick="applyGoalRecommendation()" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition">✅ 应用这些专业推荐</button>
      <button onclick="closeGoal()" class="bg-gray-100 text-gray-600 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 transition">关闭</button>
    </div>
    <div id="goal-conflict-warning" class="hidden mt-3 bg-amber-50 border border-amber-200 rounded-lg p-2 text-sm text-amber-700"></div>
  </div>

  <div class="mt-4 text-center">
    <a href="#" onclick="scrollToInput();return false;" class="text-sm text-gray-400 hover:text-blue-500">直接开始填志愿，我已有明确方向 →</a>
  </div>
</section>'''

html = html.replace('<!-- Step 1 -->', advisor_section + '\n<!-- Step 1 -->')

# 注入 GOALS JS 数据
goals_js = "const GOALS = " + json.dumps(GOALS, ensure_ascii=False) + ";"
html = html.replace("const DATA = ", goals_js + "\nconst DATA = ", 1)

# 注入 JS 逻辑
goal_js = '''
let activeGoals = [];
let currentGoalId = null;

function openGoal(id) {
  currentGoalId = id;
  var g = GOALS.find(function(x){return x.id===id;});
  if (!g) return;
  document.getElementById('goal-detail').classList.remove('hidden');
  document.getElementById('goal-detail-title').textContent = g.icon + ' ' + g.title + ' — ' + g.short;
  document.getElementById('goal-detail-content').innerHTML =
    g.analysis +
    '<div class="bg-blue-50 rounded-lg p-3 mt-2"><p class="font-medium text-blue-800 text-sm">📊 推荐专业类别</p><p class="text-sm text-blue-700 mt-1">' + g.recommend.join(' · ') + '</p><p class="text-xs text-blue-600 mt-1">' + g.reason + '</p></div>' +
    '<div class="bg-red-50 rounded-lg p-3 mt-2"><p class="font-medium text-red-800 text-sm">⚠️ 需要注意的代价</p><p class="text-sm text-red-700 mt-1">' + g.cost + '</p></div>';

  document.querySelectorAll('.goal-card').forEach(function(c){c.classList.remove('ring-2','ring-blue-400');});
  var card = document.getElementById('goal-card-'+id);
  if (card) card.classList.add('ring-2','ring-blue-400');

  if (activeGoals.length > 0) {
    var conflicts = activeGoals.filter(function(ag){return g.conflicts.includes(ag);});
    var warn = document.getElementById('goal-conflict-warning');
    if (conflicts.length > 0) {
      var conflictNames = conflicts.map(function(cid){var x=GOALS.find(function(g2){return g2.id===cid;}); return x?x.title:cid;});
      warn.classList.remove('hidden');
      warn.innerHTML = '⚠️ 你之前选了「' + conflictNames.join('」「') + '」，与「' + g.title + '」在现实中往往难以兼得。建议排个优先级。';
    } else { warn.classList.add('hidden'); }
  }

  document.getElementById('goal-detail').scrollIntoView({behavior:'smooth'});
}

function closeGoal() {
  currentGoalId = null;
  document.getElementById('goal-detail').classList.add('hidden');
  document.querySelectorAll('.goal-card').forEach(function(c){c.classList.remove('ring-2','ring-blue-400');});
}

function applyGoalRecommendation() {
  if (!currentGoalId) return;
  var g = GOALS.find(function(x){return x.id===currentGoalId;});
  if (!g) return;
  if (!activeGoals.includes(currentGoalId)) activeGoals.push(currentGoalId);
  document.querySelectorAll('#major-pref-selector .subject-chip').forEach(function(b){
    if (g.recommend.includes(b.dataset.cat)) b.classList.add('active');
  });
  updateMajorPrefDisplay();
  closeGoal();
  scrollToInput();
}

function scrollToInput() {
  document.getElementById('advisor-section').classList.add('hidden');
  document.getElementById('step-input').scrollIntoView({behavior:'smooth'});
}
'''
html = html.replace('// ==================== 位次换算 ====================', goal_js + '\n// ==================== 位次换算 ====================')

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html', 'w') as f:
    f.write(html)

print(f'Done. Size: {len(html)} chars ({len(html.encode())/1024:.0f} KB)')
