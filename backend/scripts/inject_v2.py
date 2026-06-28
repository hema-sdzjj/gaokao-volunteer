#!/usr/bin/env python3
"""
将 V2 功能注入 standalone.html:
1. 就业数据 (薪资/需求/去向/AI风险)
2. 专业偏好标签选择
3. 偏好匹配排序算法
4. 推荐卡片中的就业信息摘要
"""

import json, re

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html') as f:
    html = f.read()

# ===== 1. 就业数据 =====
EMPLOYMENT = {
    "计算机科学与技术": {
        "salary_start": 12000, "salary_5yr": 22000, "salary_10yr": 40000,
        "salary_trend": "↗ 年均+15%", "demand_12m": 85000, "demand_trend": "↗ +12%",
        "ai_risk": "🟡 中等（低端岗位减少，高端需求增加）",
        "industries": {"互联网/IT": 45, "金融科技": 18, "制造业": 12, "政府/事业单位": 8, "教育/科研": 7},
        "cities": {"北京": 22, "上海": 18, "深圳": 15, "杭州": 12, "成都": 8},
        "employers": "华为、腾讯、阿里、字节跳动、美团、银行IT部门",
        "note": "竞争激烈，头部院校与普通院校差距大。建议在校积累项目经验和实习。"
    },
    "软件工程": {
        "salary_start": 11000, "salary_5yr": 20000, "salary_10yr": 38000,
        "salary_trend": "↗ 年均+13%", "demand_12m": 72000, "demand_trend": "↗ +10%",
        "ai_risk": "🟡 中等（常规开发受AI影响，架构设计仍稀缺）",
        "industries": {"互联网/IT": 50, "金融科技": 15, "制造业": 10, "外包服务": 12, "政府/事业单位": 5},
        "cities": {"北京": 20, "上海": 17, "深圳": 16, "杭州": 14, "成都": 10},
        "employers": "腾讯、阿里、字节、百度、网易、各行业IT部门",
        "note": "与实践结合紧密，实习经历对就业影响大。"
    },
    "通信工程": {
        "salary_start": 9000, "salary_5yr": 17000, "salary_10yr": 28000,
        "salary_trend": "→ 平稳+5%", "demand_12m": 35000, "demand_trend": "→ +3%",
        "ai_risk": "🟢 低（硬件+通信协议难以被AI替代）",
        "industries": {"通信设备": 35, "运营商": 25, "互联网": 15, "军工/航天": 10, "电力": 8},
        "cities": {"深圳": 20, "北京": 18, "上海": 15, "南京": 10, "西安": 8},
        "employers": "华为、中兴、中国移动、电信、联通、大唐电信",
        "note": "5G/6G持续演进，通信+AI融合是新方向。"
    },
    "临床医学": {
        "salary_start": 6000, "salary_5yr": 12000, "salary_10yr": 25000,
        "salary_trend": "↗ 年均+10%（规培后跳升）", "demand_12m": 60000, "demand_trend": "↗ +15%",
        "ai_risk": "🟢 低（诊断辅助但决策仍需医生）",
        "industries": {"三甲医院": 40, "二甲/社区医院": 30, "民营医院": 15, "医药企业": 8, "科研机构": 5},
        "cities": {"北京": 15, "上海": 12, "广州": 10, "省会城市": 40, "地级市": 20},
        "employers": "各省市三甲医院、华西/协和/301等顶级医院、药企医学部",
        "note": "培养周期长(5年本科+3年规培)，但职业稳定性和社会地位高。学历要求持续提升。"
    },
    "口腔医学": {
        "salary_start": 8000, "salary_5yr": 18000, "salary_10yr": 35000,
        "salary_trend": "↗ 年均+18%", "demand_12m": 28000, "demand_trend": "↗ +20%",
        "ai_risk": "🟢 低（手术操作依赖人工）",
        "industries": {"口腔专科医院": 35, "综合医院口腔科": 20, "民营口腔诊所": 35, "口腔器械公司": 5},
        "cities": {"一线城市": 35, "新一线": 30, "其他": 30},
        "employers": "北大口腔、华西口腔、通策医疗、瑞尔齿科、泰康拜博",
        "note": "市场化程度高，民营诊所收入上限远超公立。近年持续热门。"
    },
    "法学": {
        "salary_start": 5500, "salary_5yr": 12000, "salary_10yr": 25000,
        "salary_trend": "→ 平稳（顶尖律所涨幅大，普通岗位一般）", "demand_12m": 45000, "demand_trend": "→ +2%",
        "ai_risk": "🟡 中等（法律检索和文书起草受AI影响）",
        "industries": {"律所": 30, "法院/检察院": 20, "企业法务": 25, "政府法制办": 10, "金融机构合规": 10},
        "cities": {"北京": 25, "上海": 20, "深圳": 12, "广州": 10, "省会": 25},
        "employers": "金杜/中伦/君合等红圈所、各级法院检察院、大型企业法务部",
        "note": "两极分化严重：五院四系毕业生与普通院校差距极大。建议考取法律职业资格证。"
    },
    "经济学": {
        "salary_start": 7000, "salary_5yr": 15000, "salary_10yr": 28000,
        "salary_trend": "→ 平稳+6%", "demand_12m": 38000, "demand_trend": "→ +4%",
        "ai_risk": "🟡 中等（数据分析部分可被AI替代）",
        "industries": {"银行/证券/保险": 35, "咨询公司": 15, "政府部门": 15, "互联网": 12, "研究机构": 8},
        "cities": {"北京": 30, "上海": 25, "深圳": 15, "广州": 10, "杭州": 8},
        "employers": "工农中建、券商研究所、麦肯锡/BCG、国家统计局等",
        "note": "宽口径专业，就业面广但需要叠加技能（数据分析、编程、CPA等）。"
    },
    "会计学": {
        "salary_start": 5500, "salary_5yr": 12000, "salary_10yr": 22000,
        "salary_trend": "→ 平稳（CPA持证者收入翻倍）", "demand_12m": 55000, "demand_trend": "→ +1%",
        "ai_risk": "🔴 较高（基础记账和审计被AI自动化取代）",
        "industries": {"会计师事务所": 30, "企业财务": 35, "银行": 15, "政府审计": 10, "税务": 8},
        "cities": {"北京": 20, "上海": 18, "深圳": 12, "广州": 10, "各省会": 30},
        "employers": "四大(普华永道/德勤/安永/毕马威)、八大内资所、各行业财务部",
        "note": "AI冲击较大，建议向管理会计、财务分析、税务筹划方向转型。CPA仍是核心壁垒。"
    },
    "机械工程": {
        "salary_start": 6500, "salary_5yr": 12000, "salary_10yr": 20000,
        "salary_trend": "→ 平稳+3%", "demand_12m": 50000, "demand_trend": "→ +2%",
        "ai_risk": "🟡 中等（智能制造需要新技能）",
        "industries": {"汽车制造": 25, "装备制造": 20, "航空航天": 12, "电子制造": 15, "能源": 10},
        "cities": {"上海": 15, "深圳": 12, "苏州": 10, "重庆": 10, "长春": 8},
        "employers": "上汽、一汽、比亚迪、三一重工、中航工业、西门子",
        "note": "传统工科，建议向智能制造、机器人、新能源汽车方向延伸。"
    },
    "车辆工程": {
        "salary_start": 8000, "salary_5yr": 16000, "salary_10yr": 28000,
        "salary_trend": "↗ 年均+12%（新能源拉动）", "demand_12m": 30000, "demand_trend": "↗ +25%",
        "ai_risk": "🟢 低（车辆硬件+系统集成）",
        "industries": {"新能源汽车": 40, "传统车企": 20, "自动驾驶": 15, "零部件": 15, "汽车电子": 8},
        "cities": {"上海": 18, "深圳": 15, "北京": 12, "合肥": 10, "广州": 10},
        "employers": "比亚迪、特斯拉、蔚来、理想、小鹏、华为车BU",
        "note": "新能源汽车爆发式增长，人才缺口大。自动驾驶方向前景好。"
    },
    "土木工程": {
        "salary_start": 5500, "salary_5yr": 10000, "salary_10yr": 18000,
        "salary_trend": "↘ 下降-5%（基建放缓、房地产下行）", "demand_12m": 25000, "demand_trend": "↘ -15%",
        "ai_risk": "🟢 低（现场施工管理难替代）",
        "industries": {"建筑施工": 35, "设计院": 20, "房地产": 15, "监理": 12, "政府建设": 10},
        "cities": {"全国分散": 60, "一线城市": 15, "新一线": 20},
        "employers": "中建、中铁、中交、万科、碧桂园、各省建工集团",
        "note": "⚠️ 行业下行期，就业压力大。建议向智能建造、BIM、绿色建筑方向转型。"
    },
    "电气工程及其自动化": {
        "salary_start": 7500, "salary_5yr": 14000, "salary_10yr": 22000,
        "salary_trend": "↗ 年均+8%（新能源电力拉动）", "demand_12m": 40000, "demand_trend": "↗ +10%",
        "ai_risk": "🟢 低（电力系统核心不可替代）",
        "industries": {"国家电网/南方电网": 35, "发电集团": 20, "新能源": 18, "电气设备制造": 15, "轨道交通": 8},
        "cities": {"各省会电力公司": 50, "北京": 10, "上海": 8, "深圳": 5, "新能源基地": 15},
        "employers": "国网、南网、华能/华电/国电投、宁德时代、施耐德、ABB",
        "note": "国网是主要去向，工作稳定待遇好。新能源储能方向是新增长点。"
    },
    "自动化": {
        "salary_start": 8000, "salary_5yr": 15000, "salary_10yr": 25000,
        "salary_trend": "↗ 年均+10%", "demand_12m": 38000, "demand_trend": "↗ +12%",
        "ai_risk": "🟡 中等（传统控制受AI影响，智能控制需求增加）",
        "industries": {"智能制造": 30, "汽车电子": 18, "机器人": 15, "能源": 12, "航空航天": 10},
        "cities": {"深圳": 18, "上海": 15, "苏州": 12, "北京": 10, "杭州": 8},
        "employers": "汇川技术、西门子、ABB、大疆、比亚迪、各智能制造企业",
        "note": "智能制造+工业4.0大趋势下前景好。建议学习Python/ROS/机器视觉。"
    },
    "英语": {
        "salary_start": 5000, "salary_5yr": 10000, "salary_10yr": 18000,
        "salary_trend": "↘ 下降（AI翻译冲击大）", "demand_12m": 30000, "demand_trend": "↘ -10%",
        "ai_risk": "🔴 高（AI翻译和写作工具冲击显著）",
        "industries": {"教育培训": 35, "外贸": 20, "翻译": 12, "跨境电商": 15, "外企": 10},
        "cities": {"北京": 18, "上海": 18, "深圳": 12, "广州": 10, "其他": 35},
        "employers": "新东方、好未来、传音控股、阿里巴巴国际站、各外企",
        "note": "⚠️ AI冲击最大的专业之一。建议叠加其他技能（法律/商务/技术写作）。"
    },
    "数学与应用数学": {
        "salary_start": 7500, "salary_5yr": 18000, "salary_10yr": 35000,
        "salary_trend": "↗ 年均+15%（AI/大数据/量化金融拉动）", "demand_12m": 32000, "demand_trend": "↗ +18%",
        "ai_risk": "🟢 低（AI底层就是数学，需求反而增加）",
        "industries": {"IT/互联网": 30, "金融量化": 20, "教育": 15, "科研": 12, "数据分析": 15},
        "cities": {"北京": 22, "上海": 20, "深圳": 15, "杭州": 10, "其他": 25},
        "employers": "量化私募(九坤/幻方)、互联网大厂AI Lab、各大银行风控部",
        "note": "AI时代受益专业。建议掌握编程(Python/R)转数据科学/量化方向。"
    },
    "社会工作": {
        "salary_start": 4000, "salary_5yr": 7000, "salary_10yr": 12000,
        "salary_trend": "→ 平稳+3%", "demand_12m": 8000, "demand_trend": "→ +5%",
        "ai_risk": "🟢 低（人际服务难以替代）",
        "industries": {"民政/社区": 40, "社工机构": 30, "NGO/基金会": 12, "医疗社工": 8, "学校社工": 5},
        "cities": {"北京": 12, "上海": 12, "广州": 10, "深圳": 10, "各省会": 40},
        "employers": "各级民政局、恩派/壹基金等公益组织、社区卫生中心",
        "note": "薪资天花板低，但考公/考编有专门通道。社会价值感强。"
    },
    "信息管理与信息系统": {
        "salary_start": 8000, "salary_5yr": 16000, "salary_10yr": 28000,
        "salary_trend": "↗ 年均+10%", "demand_12m": 25000, "demand_trend": "↗ +8%",
        "ai_risk": "🟡 中等",
        "industries": {"IT/互联网": 35, "咨询": 18, "金融": 15, "制造": 12, "政府": 10},
        "cities": {"北京": 20, "上海": 18, "深圳": 15, "杭州": 10, "成都": 8},
        "employers": "SAP/用友/金蝶等ERP厂商、互联网产品部门、四大咨询",
        "note": "交叉学科(管理+IT)，适合做产品经理、ERP顾问、数据分析师。"
    },
}

# ===== 2. 专业大类映射 =====
MAJOR_CATEGORIES = {
    "计算机类": {"keywords": ["计算机", "软件", "信息管理", "人工智能", "数据科学", "网络安全"], "color": "blue"},
    "电子信息类": {"keywords": ["通信", "电子", "信息工程", "微电子", "光电"], "color": "indigo"},
    "医学类": {"keywords": ["临床医学", "口腔", "基础医学", "麻醉", "影像", "护理"], "color": "red"},
    "法学类": {"keywords": ["法学", "法律", "知识产权", "社会工作", "政治学"], "color": "amber"},
    "经管类": {"keywords": ["经济", "会计", "财务", "金融", "工商管理", "市场营销"], "color": "green"},
    "机械电气类": {"keywords": ["机械", "车辆", "电气", "自动化", "机器人", "智能制造"], "color": "orange"},
    "师范语言类": {"keywords": ["英语", "数学", "物理", "化学", "语文", "教育", "汉语言"], "color": "purple"},
    "土木建筑类": {"keywords": ["土木", "建筑", "工程管理", "城市规划", "给排水"], "color": "stone"},
}

# ===== 3. 注入数据到 HTML =====

# 3a. 注入就业数据 (在 DATA 定义之后)
emp_js = "const EMPLOYMENT = " + json.dumps(EMPLOYMENT, ensure_ascii=False) + ";"
html = html.replace("const DATA = ", emp_js + "\nconst DATA = ", 1)

# 3b. 注入专业大类映射
cat_js = "const MAJOR_CATEGORIES = " + json.dumps(MAJOR_CATEGORIES, ensure_ascii=False) + ";"
html = html.replace("const MAJOR_CATEGORIES = ", cat_js + "\n// orig: const MAJOR_CATEGORIES = ", 1)

# Actually the MAJOR_CATEGORIES doesn't exist yet in HTML. Let me inject it after DATA.
html = html.replace("// 预处理：构建索引", "const MAJOR_CATEGORIES = " + json.dumps(MAJOR_CATEGORIES, ensure_ascii=False) + ";\n\n// 预处理：构建索引")

# 3c. 在选科区域下方添加专业偏好区域
major_pref_html = '''  <!-- 专业意向 -->
  <div class="mb-6">
    <label class="block text-sm font-medium text-gray-700 mb-2">🎯 专业意向（可选，帮系统精准推荐）</label>
    <div class="flex flex-wrap gap-2" id="major-pref-selector"></div>
    <p class="text-xs text-gray-400 mt-1">已选: <span id="major-pref-display" class="text-blue-600 font-medium">不限（系统按分数推荐）</span></p>
  </div>
'''
html = html.replace('''  <button onclick="analyze()" class="btn-primary text-lg">🔍 开始分析</button>''', major_pref_html + '''
  <button onclick="analyze()" class="btn-primary text-lg">🔍 开始分析</button>''')

# 3d. 注入专业偏好初始化JS (在 initSubjects 之后)
major_init_js = '''
(function initMajorPrefs() {
  const cats = [
    {key:'计算机类',label:'💻 计算机类',color:'blue'},
    {key:'电子信息类',label:'📡 电子信息类',color:'indigo'},
    {key:'医学类',label:'🩺 医学类',color:'red'},
    {key:'法学类',label:'⚖️ 法学类',color:'amber'},
    {key:'经管类',label:'💰 经管类',color:'green'},
    {key:'机械电气类',label:'🔧 机械电气类',color:'orange'},
    {key:'师范语言类',label:'📚 师范语言类',color:'purple'},
    {key:'土木建筑类',label:'🏗 土木建筑类',color:'stone'},
  ];
  const sel = document.getElementById('major-pref-selector');
  cats.forEach(c => {
    const btn = document.createElement('button');
    btn.className = 'subject-chip';
    btn.textContent = c.label; btn.dataset.cat = c.key;
    btn.onclick = () => {
      btn.classList.toggle('active');
      updateMajorPrefDisplay();
    };
    sel.appendChild(btn);
  });
})();
function updateMajorPrefDisplay() {
  const active = [...document.querySelectorAll('#major-pref-selector .active')].map(b=>b.dataset.cat);
  const display = document.getElementById('major-pref-display');
  display.textContent = active.length ? active.join('、') : '不限（系统按分数推荐）';
  state.preferredMajors = active;
}
function matchMajorCategory(majorName, preferredCats) {
  if (!preferredCats || !preferredCats.length) return 1.0; // 没选→全部满分
  for (const cat of preferredCats) {
    const info = MAJOR_CATEGORIES[cat];
    if (!info) continue;
    for (const kw of info.keywords) {
      if (majorName.includes(kw)) return 1.0; // 精确匹配
    }
  }
  return 0.3; // 不匹配但保留，降低权重
}
'''
html = html.replace('// ==================== 位次换算 ====================', major_init_js + '\n// ==================== 位次换算 ====================')

# 3e. 更新 recommend() 函数 — 加入偏好匹配排序
# 替换结果排序逻辑
old_sort = '''  // 排序
  results.sort((a,b) => b.probability - a.probability);'''
new_sort = '''  // 排序: 概率×0.5 + 偏好匹配×0.3 + 院校层次×0.2
  const levelScore = {'985':100,'211':80,'双一流':70,'普通':50};
  results.forEach(r => {
    r._prefMatch = matchMajorCategory(r.major_name, prefs.majorCats || []);
    r._levelScore = levelScore[r.school_level] || 50;
    r._sortScore = r.probability*0.5 + r._prefMatch*0.3 + (r._levelScore/100)*0.2;
    // 加入就业数据
    r.employment = EMPLOYMENT[r.major_name] || null;
  });
  results.sort((a,b) => b._sortScore - a._sortScore);'''
html = html.replace(old_sort, new_sort)

# 3f. 更新 analyze() → 读取专业偏好
old_prefs = "const prefs = { city: document.getElementById('pref-city').value, level: document.getElementById('pref-level').value };"
new_prefs = "const prefs = { city: document.getElementById('pref-city').value, level: document.getElementById('pref-level').value, majorCats: state.preferredMajors || [] };"
html = html.replace(old_prefs, new_prefs)

# 3g. 更新推荐卡片渲染 → 加入就业摘要 + 展开按钮
# 找到卡片渲染中 school_level 显示部分，在其后加入就业信息
old_card_end = '''            ${item.tuition?`<span>学费: <strong>${item.tuition}/年</strong></span>`:''}
          </div>
          <div class="text-xs text-gray-400 mt-1">近3年位次: ${hist}</div>
        </div>'''

new_card_end = '''            ${item.tuition?`<span>学费: <strong>${item.tuition}/年</strong></span>`:''}
            ${item._prefMatch<1?`<span class="text-orange-500 text-xs">⚠ 专业偏好不匹配</span>`:''}
          </div>
          <div class="text-xs text-gray-400 mt-1">近3年位次: ${hist}</div>
          ${item.employment ? `
          <div class="mt-2 bg-gray-50 rounded-lg p-2 text-xs">
            <div class="flex flex-wrap gap-3">
              <span>💰 应届起薪: <strong>¥${(item.employment.salary_start/1000).toFixed(0)}K</strong></span>
              <span>📈 需求: <strong>${item.employment.demand_trend}</strong></span>
              <span>🤖 AI风险: <strong>${item.employment.ai_risk}</strong></span>
              <button onclick="toggleEmpDetail(this)" class="text-blue-500 hover:text-blue-700 ml-auto">展开详情 ▾</button>
            </div>
            <div class="emp-detail hidden mt-2 pt-2 border-t border-gray-200">
              <p>💼 5年经验薪资: ¥${item.employment.salary_5yr.toLocaleString()} | 10年+: ¥${item.employment.salary_10yr.toLocaleString()}</p>
              <p>🏢 主要去向: ${Object.entries(item.employment.industries).map(([k,v])=>k+' '+v+'%').join(' | ')}</p>
              <p>🌆 城市: ${Object.entries(item.employment.cities).map(([k,v])=>k+' '+v+'%').join(' | ')}</p>
              <p>🏭 典型雇主: ${item.employment.employers}</p>
              <p class="text-gray-500 mt-1">💬 ${item.employment.note}</p>
              <p class="text-gray-400 mt-1">📊 薪资趋势: ${item.employment.salary_trend}</p>
            </div>
          </div>` : ''}
        </div>'''
html = html.replace(old_card_end, new_card_end)

# 3h. 注入就业详情展开/收起函数
emp_toggle_js = '''
function toggleEmpDetail(btn) {
  const detail = btn.parentElement.parentElement.querySelector('.emp-detail');
  if (detail.classList.contains('hidden')) {
    detail.classList.remove('hidden');
    btn.textContent = '收起 ▴';
  } else {
    detail.classList.add('hidden');
    btn.textContent = '展开详情 ▾';
  }
}
'''
html = html.replace('function scrollTo(el)', emp_toggle_js + '\nfunction scrollTo(el)')

# 3i. 初始化 state 中加入 preferredMajors
html = html.replace("subjects: ['物理'],", "subjects: ['物理'], preferredMajors: [],")

with open('/Users/hema/gaokao-volunteer/frontend/standalone.html', 'w') as f:
    f.write(html)

print(f'Done. HTML size: {len(html)} chars ({len(html.encode())/1024:.0f} KB)')
