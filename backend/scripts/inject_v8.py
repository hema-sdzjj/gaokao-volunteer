#!/usr/bin/env python3
"""V8: P0优化 — 一键决策建议 + 下行专业主动警告"""
import re

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html') as f:
    html = f.read()

# ===== 1. 在推荐结果区加入决策建议卡片 =====
decision_card = '''
    <!-- 决策建议卡片 -->
    <div id="decision-summary" class="card p-5 mb-6 hidden animate-in bg-gradient-to-r from-amber-50 via-white to-blue-50 border-l-4 border-amber-400">
      <div class="flex items-start gap-3">
        <span class="text-3xl">🧓</span>
        <div class="flex-1">
          <h3 class="text-lg font-bold text-gray-800 mb-1">如果我是你，我会重点看这三个方向</h3>
          <p class="text-sm text-gray-500 mb-4">基于你的分数、偏好和就业市场数据，以下是综合推荐。每个人情况不同，最终决定权在你手里。</p>
          <div id="decision-content" class="space-y-3"></div>
        </div>
      </div>
    </div>
'''
html = html.replace('<div id="rec-list"', decision_card + '\n<div id="rec-list"')

# ===== 2. 决策建议生成逻辑 =====
decision_js = '''
function generateDecision(recs, myRank, prefs) {
  // 从所有推荐中选出最佳3个：1个稳/保(优先)，1个优选(就业好)，1个冲(值得试)
  var all = [];
  ['reach','match','safety'].forEach(function(k){
    (recs[k]||[]).forEach(function(r){ all.push(r); });
  });
  if (all.length < 3) return null;

  // 排序：综合分 = 概率×0.3 + 就业前景×0.3 + 院校层次×0.2 + 偏好匹配×0.2
  var levelScore={'985':5,'211':4,'双一流':3,'普通':2};
  all.forEach(function(r){
    var empScore = 0;
    if (r.employment) {
      if (r.employment.salary_start >= 10000) empScore += 2;
      else if (r.employment.salary_start >= 7000) empScore += 1;
      if (TREND_DATA && TREND_DATA[r.major_name]) {
        var t = TREND_DATA[r.major_name];
        if (t.trend_4yr.indexOf('强劲')>=0||t.trend_4yr.indexOf('增长')>=0) empScore += 2;
        else if (t.trend_4yr.indexOf('平稳')>=0) empScore += 1;
        if (t.ai_resilience==='高'||t.ai_resilience==='极高') empScore += 1;
        if (t.saturation==='低') empScore += 1;
      }
    }
    r._decisionScore = r.probability*0.3 + (empScore/6)*0.3 + ((levelScore[r.school_level]||2)/5)*0.2 + (r._prefMatch||1)*0.2;
  });
  all.sort(function(a,b){return b._decisionScore - a._decisionScore;});

  // 选择3个代表性建议：一个高概率保底、一个高回报、一个值得冲
  var picked = [];
  var safety = all.filter(function(r){return r.probability>=0.65;});
  var good = all.filter(function(r){return r.probability>=0.25 && r.probability<0.65;});
  var reach = all.filter(function(r){return r.probability>=0.05 && r.probability<0.25;});

  if (safety.length>0) picked.push({item:safety[0],reason:'保底首选，录取把握大'});
  if (good.length>0) picked.push({item:good[0],reason:'性价比最高，分数匹配+就业好'});
  if (reach.length>0 && reach[0]._decisionScore > 0.4) picked.push({item:reach[0],reason:'值得一冲，录上就赚'});

  // 如果不够3个，用最高分的补
  for (var i=0; i<all.length&&picked.length<3; i++) {
    if (!picked.some(function(p){return p.item.id===all[i].id;})) {
      picked.push({item:all[i],reason:'综合评分高，值得考虑'});
    }
  }
  return picked.slice(0,3);
}

function renderDecision(picked, myRank) {
  var card = document.getElementById('decision-summary');
  if (!picked || picked.length===0) { card.classList.add('hidden'); return; }
  card.classList.remove('hidden');
  document.getElementById('decision-content').innerHTML = picked.map(function(p,i){
    var r=p.item;
    var icons=['🥇','🥈','🥉'];
    var trendHtml='';
    if (TREND_DATA && TREND_DATA[r.major_name]) {
      var t=TREND_DATA[r.major_name];
      var trendIcon=t.trend_4yr.indexOf('强劲')>=0?'🔥':t.trend_4yr.indexOf('增长')>=0?'📈':t.trend_4yr.indexOf('下行')>=0||t.trend_4yr.indexOf('下降')>=0?'⚠️':'➡️';
      var aiIcon=t.ai_resilience==='高'||t.ai_resilience==='极高'?'🛡️':t.ai_resilience==='中'?'⚡':'🔴';
      trendHtml='<span class="text-xs">'+trendIcon+' '+t.trend_4yr+'</span><span class="text-xs ml-2">'+aiIcon+' AI抵抗:'+t.ai_resilience+'</span>';
    }
    var warnBadge='';
    if (TREND_DATA && TREND_DATA[r.major_name]) {
      var t=TREND_DATA[r.major_name];
      if (t.saturation==='极高'||t.ai_resilience==='极低'||(t.trend_4yr.indexOf('下行')>=0||t.trend_4yr.indexOf('下降')>=0)) {
        warnBadge='<span class="tag-reach ml-1">需谨慎</span>';
      }
    }
    return '<div class="flex items-start gap-3 bg-white rounded-lg p-3 border">'+
      '<span class="text-xl">'+icons[i]+'</span>'+
      '<div class="flex-1">'+
        '<p class="font-semibold">'+r.school_name+' · '+r.major_name+' '+warnBadge+'</p>'+
        '<p class="text-xs text-gray-500 mt-1">录取概率 <strong>'+(r.probability*100).toFixed(0)+'%</strong> · '+
          (r.employment?'起薪 ¥'+(r.employment.salary_start/1000).toFixed(0)+'K · ':'')+
          (r.school_level||'')+' · '+ (r.school_city||'')+
        '</p>'+
        '<p class="text-xs text-gray-500">'+trendHtml+'</p>'+
        '<p class="text-xs text-amber-700 mt-1">💡 '+p.reason+'</p>'+
      '</div>'+
      '<button onclick="addVolFromDecision(\''+r.id+'\')" class="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded hover:bg-blue-100">+ 加入志愿表</button>'+
    '</div>';
  }).join('');
}

function addVolFromDecision(id) {
  addVol(id);
  document.getElementById('decision-summary').scrollIntoView({behavior:'smooth'});
}
'''

html = html.replace('// ==================== UI渲染 ====================', decision_js + '\n// ==================== UI渲染 ====================')

# ===== 3. 在 analyze() 的 setTimeout 中调用决策生成 =====
old_after_render = '''state.recs = { reach: result.reach, match: result.match, safety: result.safety };
      stepIndicator(2);
      renderRank(result);
      showTab('reach');'''

new_after_render = '''state.recs = { reach: result.reach, match: result.match, safety: result.safety };
      stepIndicator(2);
      renderRank(result);
      var picked = generateDecision(state.recs, state.myRank.rank, prefs);
      renderDecision(picked, state.myRank.rank);
      showTab('reach');'''

html = html.replace(old_after_render, new_after_render)

# ===== 4. 下行专业主动警告 =====
# 在就业摘要中加入醒目的警告标签
old_emp_risk = '<span>🤖 AI风险: <strong>${item.employment.ai_risk}</strong></span>'
new_emp_risk = '''<span>🤖 AI风险: <strong>${item.employment.ai_risk}</strong></span>
              ${(function(){var t=TREND_DATA[item.major_name];if(t&&(t.saturation==='极高'||t.ai_resilience==='极低'||t.trend_4yr.indexOf('下行')>=0||t.trend_4yr.indexOf('下降')>=0))return'<span class=\"bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold animate-pulse\">⚠️ 四年后风险: 该专业就业市场正在萎缩</span>';return'';})()}'''

# 注意：旧的模板已经在V7中被替换了，现在搜索的是4项的新模板
html = html.replace('<span>AI抵抗力: <strong>${(function(){var t=TREND_DATA[item.major_name];return t?t.ai_resilience:\'-\';})()}</strong></span>',
                     '<span>AI抵抗力: <strong>${(function(){var t=TREND_DATA[item.major_name];return t?t.ai_resilience:\'-\';})()}</strong></span>' +
                     '${(function(){var t=TREND_DATA[item.major_name];if(t&&(t.saturation===\'极高\'||t.ai_resilience===\'极低\'||(t.trend_4yr.indexOf(\'下行\')>=0||t.trend_4yr.indexOf(\'下降\')>=0)))return\'<span class=\"bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold animate-pulse\">⚠️ 该专业就业市场正在萎缩，请谨慎考虑</span>\';return\'\';})()}')

# ===== 5. 加入志愿表时的二次确认 =====
# 修改addVol，对风险专业弹出确认框
old_addVol = '''function addVol(id) {
  if (state.volunteers.length >= 96) { alert('已达96个上限'); return; }
  let item = null;
  for (const k of ['reach','match','safety']) { item = state.recs[k].find(r=>r.id===id); if (item) break; }
  if (!item) return;'''

new_addVol = '''function addVol(id) {
  if (state.volunteers.length >= 96) { alert('已达96个上限'); return; }
  let item = null;
  for (const k of ['reach','match','safety']) { item = state.recs[k].find(r=>r.id===id); if (item) break; }
  if (!item) return;
  // 下行专业风险确认
  var t = TREND_DATA && TREND_DATA[item.major_name];
  if (t && (t.saturation==='极高'||t.ai_resilience==='极低'||t.trend_4yr.indexOf('下行')>=0||t.trend_4yr.indexOf('下降')>=0)) {
    if (!confirm('⚠️ 风险提醒\\n\\n「'+item.major_name+'」的就业市场正在萎缩。\\n\\n· 趋势: '+t.trend_4yr+'\\n· 人才饱和: '+t.saturation+'\\n· AI抵抗力: '+t.ai_resilience+'\\n\\n这个专业四年后可能面临较大的就业压力。\\n\\n确定要加入志愿表吗？')) return;
  }'''

html = html.replace(old_addVol, new_addVol)

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html', 'w') as f:
    f.write(html)

print(f'Done. {len(html)} chars ({len(html.encode())/1024:.0f} KB)')
