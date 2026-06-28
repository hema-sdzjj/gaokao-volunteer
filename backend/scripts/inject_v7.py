#!/usr/bin/env python3
"""
V7: 出口对比(四年后回报) + 趋势预测(上升/下降/AI冲击/2030展望)
"""
import json, re

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html') as f:
    html = f.read()

# ===== 1. 就业趋势预测数据 =====
TREND_DATA = {
    "计算机科学与技术": {"trend_4yr":"↗ 持续增长","outlook_2030":"需求+25%（AI/数字化推动）","saturation":"中高（供给大增，顶尖人才稀缺）","salary_growth":"高","ai_resilience":"中"},
    "软件工程": {"trend_4yr":"↗ 增长","outlook_2030":"需求+20%","saturation":"中高","salary_growth":"中高","ai_resilience":"中"},
    "通信工程": {"trend_4yr":"→ 平稳","outlook_2030":"需求+5%（5G/6G成熟后增速放缓）","saturation":"中","salary_growth":"中","ai_resilience":"高"},
    "临床医学": {"trend_4yr":"↗ 稳定增长","outlook_2030":"需求+20%（老龄化+医疗资源扩张）","saturation":"低（培养周期长，供给受限）","salary_growth":"中（规培后跳升）","ai_resilience":"高"},
    "口腔医学": {"trend_4yr":"↗ 快速增长","outlook_2030":"需求+35%（口腔健康意识提升+民营扩张）","saturation":"低","salary_growth":"高","ai_resilience":"高"},
    "法学": {"trend_4yr":"→ 平稳偏降","outlook_2030":"传统法学需求持平，合规/数据法增长","saturation":"高（毕业生供过于求）","salary_growth":"两极分化","ai_resilience":"中低"},
    "经济学": {"trend_4yr":"→ 平稳","outlook_2030":"需求+8%（数据分析方向增长）","saturation":"中高","salary_growth":"中","ai_resilience":"中"},
    "会计学": {"trend_4yr":"↘ 下降","outlook_2030":"基础岗位-20%（AI替代），管理会计+15%","saturation":"极高","salary_growth":"低（CPA持证者除外）","ai_resilience":"低"},
    "机械工程": {"trend_4yr":"→ 平稳","outlook_2030":"传统机械持平，智能制造+15%","saturation":"中","salary_growth":"中","ai_resilience":"中高"},
    "车辆工程": {"trend_4yr":"↗ 强劲增长","outlook_2030":"需求+40%（新能源+自动驾驶双驱动）","saturation":"低","salary_growth":"高","ai_resilience":"高"},
    "土木工程": {"trend_4yr":"↘ 持续下行","outlook_2030":"需求-20%（基建放缓+房地产收缩）","saturation":"高","salary_growth":"低","ai_resilience":"高"},
    "电气工程及其自动化": {"trend_4yr":"↗ 增长","outlook_2030":"需求+18%（新能源电力+储能）","saturation":"中","salary_growth":"中高","ai_resilience":"高"},
    "自动化": {"trend_4yr":"↗ 增长","outlook_2030":"需求+20%（智能制造+机器人）","saturation":"中","salary_growth":"中高","ai_resilience":"中高"},
    "英语": {"trend_4yr":"↘ 明显下降","outlook_2030":"传统翻译/教学-30%，复合型人才有出路","saturation":"极高","salary_growth":"低","ai_resilience":"极低"},
    "数学与应用数学": {"trend_4yr":"↗ 强劲增长","outlook_2030":"需求+30%（AI/大数据/量化金融底层驱动）","saturation":"低","salary_growth":"高","ai_resilience":"极高"},
    "社会工作": {"trend_4yr":"→ 平稳","outlook_2030":"需求+10%（社会治理重视度提升）","saturation":"低","salary_growth":"低","ai_resilience":"高"},
    "信息管理与信息系统": {"trend_4yr":"↗ 增长","outlook_2030":"需求+15%（企业数字化转型）","saturation":"中","salary_growth":"中高","ai_resilience":"中"},
}

# ===== 2. 注入趋势数据 =====
trend_js = "const TREND_DATA = " + json.dumps(TREND_DATA, ensure_ascii=False) + ";"
html = html.replace("const EMPLOYMENT = ", trend_js + "\nconst EMPLOYMENT = ", 1)

# ===== 3. 更新院校对比工具 — 加入出口对比维度 =====
# 找到 doCompare 函数中的 dimensions 数组
old_dims = '''  const dimensions = [
    {key:'level',label:'院校层次',get:s=>schoolMap[s]?.level||'-'},
    {key:'city',label:'城市',get:s=>schoolMap[s]?.city||'-'},
    {key:'grade',label:'最佳学科评估',get:s=>SCHOOL_DETAIL[s]?.grade||'-'},
    {key:'grad_rate',label:'保研率',get:s=>((SCHOOL_DETAIL[s]?.grad_rate||0)*100).toFixed(0)+'%'},
    {key:'dorm',label:'宿舍条件',get:s=>'★'.repeat(SCHOOL_DETAIL[s]?.dorm||0)+'☆'.repeat(5-(SCHOOL_DETAIL[s]?.dorm||0))},
    {key:'major_change',label:'转专业难度',get:s=>SCHOOL_DETAIL[s]?.major_change||'-'},
    {key:'founded',label:'建校/合并',get:s=>SCHOOL_DETAIL[s]?.founded||'-'},
    {key:'campus',label:'校区',get:s=>SCHOOL_DETAIL[s]?.campus||'-'},
  ];'''

new_dims = '''  const dimensions = [
    {key:'level',label:'院校层次',get:s=>schoolMap[s]?.level||'-',group:'入口'},
    {key:'city',label:'城市',get:s=>schoolMap[s]?.city||'-',group:'入口'},
    {key:'grade',label:'最佳学科评估',get:s=>SCHOOL_DETAIL[s]?.grade||'-',group:'入口'},
    {key:'grad_rate',label:'保研率',get:s=>((SCHOOL_DETAIL[s]?.grad_rate||0)*100).toFixed(0)+'%',group:'入口'},
    {key:'dorm',label:'宿舍条件',get:s=>'★'.repeat(SCHOOL_DETAIL[s]?.dorm||0)+'☆'.repeat(5-(SCHOOL_DETAIL[s]?.dorm||0)),group:'入口'},
    {key:'major_change',label:'转专业难度',get:s=>SCHOOL_DETAIL[s]?.major_change||'-',group:'入口'},
    {key:'founded',label:'建校/合并',get:s=>SCHOOL_DETAIL[s]?.founded||'-',group:'入口'},
    {key:'campus',label:'校区',get:s=>SCHOOL_DETAIL[s]?.campus||'-',group:'入口'},
    // 出口对比维度
    {key:'salary_outlook',label:'💰 四年后应届起薪(估)',get:function(s){
      var emp=null; for(var k in state.recs){var found=state.recs[k].find(function(r){return r.school_name===s&&r.employment;}); if(found){emp=found.employment;break;}}
      if(!emp) return '-';
      var trend=TREND_DATA[emp.major_name];
      if(!trend) return '¥'+(emp.salary_start/1000).toFixed(0)+'K';
      var growth=trend.salary_growth==='高'?1.2:trend.salary_growth==='中高'?1.12:trend.salary_growth==='中'?1.06:trend.salary_growth==='低'?1.02:1.0;
      return '¥'+(emp.salary_start*growth/1000).toFixed(0)+'K（'+trend.salary_growth+'增长）';
    },group:'出口'},
    {key:'industry_outlook',label:'📈 行业四年后前景',get:function(s){
      var emp=null; for(var k in state.recs){var found=state.recs[k].find(function(r){return r.school_name===s&&r.employment;}); if(found){emp=found.employment;break;}}
      if(!emp) return '-';
      var trend=TREND_DATA[emp.major_name];
      return trend?trend.outlook_2030:emp.demand_trend||'-';
    },group:'出口'},
    {key:'ai_risk_score',label:'🤖 AI冲击抵抗力',get:function(s){
      var emp=null; for(var k in state.recs){var found=state.recs[k].find(function(r){return r.school_name===s&&r.employment;}); if(found){emp=found.employment;break;}}
      if(!emp) return '-';
      var trend=TREND_DATA[emp.major_name];
      return trend?trend.ai_resilience:'-';
    },group:'出口'},
    {key:'saturation',label:'📊 人才饱和程度',get:function(s){
      var emp=null; for(var k in state.recs){var found=state.recs[k].find(function(r){return r.school_name===s&&r.employment;}); if(found){emp=found.employment;break;}}
      if(!emp) return '-';
      var trend=TREND_DATA[emp.major_name];
      return trend?trend.saturation:'-';
    },group:'出口'},
  ];'''

html = html.replace(old_dims, new_dims)

# ===== 4. 对比表格支持分组标题 =====
# 更新表格渲染逻辑以支持 group
old_table_render = '''  let table = '<div class="overflow-x-auto"><table class="w-full text-sm"><thead><tr><th class="p-2 border-b text-left">维度</th>';
  compareSchools.forEach(s => { table += '<th class="p-2 border-b text-center font-medium">'+s+'</th>'; });
  table += '</tr></thead><tbody>';
  dimensions.forEach(d => {
    table += '<tr><td class="p-2 border-b text-gray-500">'+d.label+'</td>';
    compareSchools.forEach(s => { table += '<td class="p-2 border-b text-center">'+d.get(s)+'</td>'; });
    table += '</tr>';
  });
  table += '</tbody></table></div>';'''

new_table_render = '''  var lastGroup='';
  var table = '<div class="overflow-x-auto"><table class="w-full text-sm"><thead><tr><th class="p-2 border-b text-left">维度</th>';
  compareSchools.forEach(function(s){ table += '<th class="p-2 border-b text-center font-medium">'+s+'</th>'; });
  table += '</tr></thead><tbody>';
  dimensions.forEach(function(d){
    if(d.group && d.group!==lastGroup){
      lastGroup=d.group;
      var label = lastGroup==='入口'?'📥 入学阶段':lastGroup==='出口'?'📤 毕业四年后回报':'';
      table += '<tr><td colspan="'+(compareSchools.length+1)+'" class="p-2 bg-blue-50 font-medium text-sm text-blue-700">'+label+'</td></tr>';
    }
    table += '<tr><td class="p-2 border-b text-gray-500">'+d.label+'</td>';
    compareSchools.forEach(function(s){ table += '<td class="p-2 border-b text-center">'+d.get(s)+'</td>'; });
    table += '</tr>';
  });
  table += '</tbody></table></div>';'''

html = html.replace(old_table_render, new_table_render)

# ===== 5. 就业卡片中加入趋势信息 =====
# 在就业摘要中加入趋势标签
old_emp_summary = '''<span>💰 应届起薪: <strong>¥${(item.employment.salary_start/1000).toFixed(0)}K</strong></span>
              <span>📈 需求: <strong>${item.employment.demand_trend}</strong></span>
              <span>🤖 AI风险: <strong>${item.employment.ai_risk}</strong></span>'''

new_emp_summary = '''<span>💰 应届起薪: <strong>¥${(item.employment.salary_start/1000).toFixed(0)}K</strong></span>
              <span>四年趋势: <strong>${(function(){var t=TREND_DATA[item.major_name];return t?t.trend_4yr:item.employment.demand_trend;})()}</strong></span>
              <span>饱和: <strong>${(function(){var t=TREND_DATA[item.major_name];return t?t.saturation:'-';})()}</strong></span>
              <span>AI抵抗力: <strong>${(function(){var t=TREND_DATA[item.major_name];return t?t.ai_resilience:'-';})()}</strong></span>'''

html = html.replace(old_emp_summary, new_emp_summary)

# ===== 6. 就业详情中加入2030展望 =====
old_emp_salary_trend = '<p class="text-gray-400 mt-1">📊 薪资趋势: ${item.employment.salary_trend}</p>'
new_emp_salary_trend = '''<p class="text-gray-400 mt-1">📊 薪资趋势: ${item.employment.salary_trend}</p>
            ${(function(){var t=TREND_DATA[item.major_name];if(!t)return '';return '<div class=\"mt-2 bg-gradient-to-r from-amber-50 to-blue-50 rounded-lg p-2 text-xs\"><p class=\"font-medium text-amber-800\">🔮 四年后展望（2030年）</p><p class=\"text-gray-700 mt-1\">📈 '+t.outlook_2030+'</p><p class=\"text-gray-700\">🏫 人才市场: '+t.saturation+'饱和</p><p class=\"text-gray-700\">🤖 AI抵抗力: '+t.ai_resilience+'</p></div>';})()}'''

html = html.replace(old_emp_salary_trend, new_emp_salary_trend)

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html', 'w') as f:
    f.write(html)

print(f'Done. {len(html)} chars ({len(html.encode())/1024:.0f} KB)')
