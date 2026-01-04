// 牙周病学知识图谱初始化脚本
// 所有标签使用 yzbx_ 前缀

// ==================== 模块节点 ====================
CREATE (m1:yzbx_Module {id: 'M1', name: '生物学基础', description: '牙周组织的解剖结构和生理功能基础'})
CREATE (m2:yzbx_Module {id: 'M2', name: '病因与发病机制', description: '牙周病的致病因素和发生发展机制'})
CREATE (m3:yzbx_Module {id: 'M3', name: '诊断与分类', description: '牙周病的检查方法和分类标准'})
CREATE (m4:yzbx_Module {id: 'M4', name: '治疗', description: '牙周病的各种治疗方法'})
CREATE (m5:yzbx_Module {id: 'M5', name: '预防与维护', description: '牙周病的预防措施和长期维护治疗'})

// ==================== 章节节点 ====================
// 模块1 - 生物学基础
CREATE (c1_1:yzbx_Chapter {id: 'C1_1', name: '牙周组织解剖', module_id: 'M1', description: '牙周组织包括牙龈、牙周膜、牙槽骨和牙骨质四部分，是牙齿的支持组织。理解其解剖结构是学习牙周病学的基础。'})
CREATE (c1_2:yzbx_Chapter {id: 'C1_2', name: '牙周组织生理', module_id: 'M1', description: '牙周组织具有保护、支持、感觉和修复再生功能。龈沟液、牙周膜等的生理功能对维持口腔健康至关重要。'})

// 模块2 - 病因与发病机制
CREATE (c2_1:yzbx_Chapter {id: 'C2_1', name: '牙菌斑生物膜', module_id: 'M2', description: '牙菌斑是牙周病的始动因子，以生物膜形式存在，对抗生素有耐药性。理解其形成过程和结构对防治牙周病很重要。'})
CREATE (c2_2:yzbx_Chapter {id: 'C2_2', name: '局部促进因素', module_id: 'M2', description: '牙石、食物嵌塞、不良修复体等局部因素会促进菌斑堆积和牙周破坏，临床上需要识别并去除这些因素。'})

// 模块3 - 诊断与分类
CREATE (c3_1:yzbx_Chapter {id: 'C3_1', name: '牙周检查', module_id: 'M3', description: '牙周检查是诊断的基础，包括探诊、附着丧失测量等，需要掌握标准化的检查方法和记录方式。'})
CREATE (c3_2:yzbx_Chapter {id: 'C3_2', name: '牙周病分类', module_id: 'M3', description: '2018年新分类采用分期分级系统，更科学地评估疾病严重程度和进展风险，指导治疗计划制定。'})

// 模块4 - 治疗
CREATE (c4_1:yzbx_Chapter {id: 'C4_1', name: '牙周基础治疗', module_id: 'M4', description: '包括龈上洁治、龈下刮治和根面平整，是所有牙周治疗的基础，约80%的牙周炎患者可通过基础治疗控制。'})
CREATE (c4_2:yzbx_Chapter {id: 'C4_2', name: '牙周手术治疗', module_id: 'M4', description: '用于基础治疗后仍存在深袋或骨缺损的患者，包括翻瓣术、植骨术、引导组织再生等。'})

// 模块5 - 预防与维护
CREATE (c5_1:yzbx_Chapter {id: 'C5_1', name: '牙周病预防', module_id: 'M5', description: '预防是最经济有效的策略，通过正确的口腔卫生习惯可预防大部分牙周病，重点是菌斑控制。'})
CREATE (c5_2:yzbx_Chapter {id: 'C5_2', name: '牙周维护治疗', module_id: 'M5', description: '牙周炎是慢性病，需要终身维护。SPT（支持性牙周治疗）对防止复发至关重要，复查周期一般3-6个月。'})

// ==================== 知识点节点 ====================
// 模块1 - 牙周组织解剖
CREATE (k1:yzbx_Knowledge {id: 'KP_M1_C1_1', name: '牙龈结构', chapter_id: 'C1_1', description: '包括游离龈、附着龈和龈乳头三部分。游离龈形成龈沟，正常深度0.5-3mm。', importance: 'high'})
CREATE (k2:yzbx_Knowledge {id: 'KP_M1_C1_2', name: '牙周膜组成', chapter_id: 'C1_1', description: '主要由胶原纤维束、细胞成分和基质组成。纤维束分为6组，提供牙齿支持。', importance: 'high'})
CREATE (k3:yzbx_Knowledge {id: 'KP_M1_C1_3', name: '牙槽骨特征', chapter_id: 'C1_1', description: '分为固有牙槽骨和支持骨。X线上固有牙槽骨呈硬骨板（骨白线）。', importance: 'high'})
CREATE (k4:yzbx_Knowledge {id: 'KP_M1_C1_4', name: '牙骨质类型', chapter_id: 'C1_1', description: '分为无细胞纤维性牙骨质（颈1/3）和有细胞纤维性牙骨质（根尖1/3）。', importance: 'medium'})

// 模块1 - 牙周组织生理
CREATE (k5:yzbx_Knowledge {id: 'KP_M1_C2_1', name: '龈沟液功能', chapter_id: 'C1_2', description: '含有免疫球蛋白、补体、白细胞等，具有冲洗和抗菌防御作用。', importance: 'high'})
CREATE (k6:yzbx_Knowledge {id: 'KP_M1_C2_2', name: '牙周韧带力学', chapter_id: 'C1_2', description: '可承受咀嚼力，具有本体感觉，调节咬合力大小。', importance: 'medium'})
CREATE (k7:yzbx_Knowledge {id: 'KP_M1_C2_3', name: '骨改建机制', chapter_id: 'C1_2', description: '成骨细胞与破骨细胞平衡，受机械力和炎症因子调控。', importance: 'high'})

// 模块2 - 牙菌斑生物膜
CREATE (k8:yzbx_Knowledge {id: 'KP_M2_C1_1', name: '菌斑形成过程', chapter_id: 'C2_1', description: '获得性膜形成→早期定植菌黏附→共聚集→成熟生物膜，约需7-14天。', importance: 'high'})
CREATE (k9:yzbx_Knowledge {id: 'KP_M2_C1_2', name: '致病菌种类', chapter_id: 'C2_1', description: '主要包括牙龈卟啉单胞菌(Pg)、放线聚集杆菌(Aa)、福赛坦氏菌(Tf)等红色复合体。', importance: 'high'})
CREATE (k10:yzbx_Knowledge {id: 'KP_M2_C1_3', name: '生物膜结构', chapter_id: 'C2_1', description: '由细菌、胞外多糖基质、水通道组成，具有抗生素耐药性。', importance: 'medium'})

// 模块2 - 局部促进因素
CREATE (k11:yzbx_Knowledge {id: 'KP_M2_C2_1', name: '牙石形成', chapter_id: 'C2_2', description: '菌斑矿化形成，龈上牙石主要来自唾液，龈下牙石来自龈沟液。', importance: 'high'})
CREATE (k12:yzbx_Knowledge {id: 'KP_M2_C2_2', name: '食物嵌塞', chapter_id: 'C2_2', description: '分为垂直型和水平型，可导致局部牙周破坏，需去除病因。', importance: 'medium'})
CREATE (k13:yzbx_Knowledge {id: 'KP_M2_C2_3', name: '不良修复体', chapter_id: 'C2_2', description: '悬突、边缘不密合等导致菌斑滞留，需重新修复。', importance: 'medium'})

// 模块3 - 牙周检查
CREATE (k14:yzbx_Knowledge {id: 'KP_M3_C1_1', name: '探诊技术', chapter_id: 'C3_1', description: '使用牙周探针，力度20-25g，记录6个位点探诊深度。', importance: 'high'})
CREATE (k15:yzbx_Knowledge {id: 'KP_M3_C1_2', name: '附着丧失测量', chapter_id: 'C3_1', description: 'CAL=探诊深度-釉牙骨质界到龈缘距离，反映累积破坏。', importance: 'high'})
CREATE (k16:yzbx_Knowledge {id: 'KP_M3_C1_3', name: '牙周图表制作', chapter_id: 'C3_1', description: '记录探诊深度、出血、松动度等，便于治疗计划和随访。', importance: 'medium'})

// 模块3 - 牙周病分类
CREATE (k17:yzbx_Knowledge {id: 'KP_M3_C2_1', name: '牙龈炎分类', chapter_id: 'C3_2', description: '包括菌斑性和非菌斑性牙龈病，前者最常见。', importance: 'high'})
CREATE (k18:yzbx_Knowledge {id: 'KP_M3_C2_2', name: '牙周炎分期', chapter_id: 'C3_2', description: '2018新分类采用分期(I-IV)和分级(A-C)系统。', importance: 'high'})
CREATE (k19:yzbx_Knowledge {id: 'KP_M3_C2_3', name: '新分类标准', chapter_id: 'C3_2', description: '基于附着丧失、骨吸收、失牙数分期；基于进展速率分级。', importance: 'high'})

// 模块4 - 牙周基础治疗
CREATE (k20:yzbx_Knowledge {id: 'KP_M4_C1_1', name: '龈上洁治', chapter_id: 'C4_1', description: '去除龈上牙石和菌斑，使用超声或手工器械。', importance: 'high'})
CREATE (k21:yzbx_Knowledge {id: 'KP_M4_C1_2', name: '龈下刮治', chapter_id: 'C4_1', description: '深入牙周袋清除龈下牙石和感染牙骨质。', importance: 'high'})
CREATE (k22:yzbx_Knowledge {id: 'KP_M4_C1_3', name: '根面平整', chapter_id: 'C4_1', description: '使刮治后根面光滑，利于牙周组织再附着。', importance: 'high'})

// 模块4 - 牙周手术治疗
CREATE (k23:yzbx_Knowledge {id: 'KP_M4_C2_1', name: '翻瓣术', chapter_id: 'C4_2', description: '切开牙龈、翻瓣暴露病变区进行清创，常见改良Widman翻瓣术。', importance: 'high'})
CREATE (k24:yzbx_Knowledge {id: 'KP_M4_C2_2', name: '植骨术', chapter_id: 'C4_2', description: '在骨缺损区填入骨替代材料，促进骨再生。', importance: 'medium'})
CREATE (k25:yzbx_Knowledge {id: 'KP_M4_C2_3', name: '引导再生', chapter_id: 'C4_2', description: '使用屏障膜引导牙周组织选择性再生。', importance: 'medium'})

// 模块5 - 牙周病预防
CREATE (k26:yzbx_Knowledge {id: 'KP_M5_C1_1', name: '口腔卫生宣教', chapter_id: 'C5_1', description: '教授Bass刷牙法，使用牙线/牙间刷，定期专业维护。', importance: 'high'})
CREATE (k27:yzbx_Knowledge {id: 'KP_M5_C1_2', name: '刷牙方法', chapter_id: 'C5_1', description: '推荐Bass法或改良Bass法，每天2次，每次2分钟。', importance: 'high'})
CREATE (k28:yzbx_Knowledge {id: 'KP_M5_C1_3', name: '辅助工具', chapter_id: 'C5_1', description: '包括牙线、牙间刷、冲牙器等，根据牙间隙选择。', importance: 'medium'})

// 模块5 - 牙周维护治疗
CREATE (k29:yzbx_Knowledge {id: 'KP_M5_C2_1', name: '复查周期', chapter_id: 'C5_2', description: '牙周炎患者建议3-6个月复查一次，高危患者更频繁。', importance: 'high'})
CREATE (k30:yzbx_Knowledge {id: 'KP_M5_C2_2', name: 'SPT原则', chapter_id: 'C5_2', description: '支持性牙周治疗，终身维护，定期评估和必要的再治疗。', importance: 'high'})
CREATE (k31:yzbx_Knowledge {id: 'KP_M5_C2_3', name: '长期管理', chapter_id: 'C5_2', description: '监测探诊深度、出血指数，及时发现复发。', importance: 'medium'})

// ==================== 能力节点 ====================
CREATE (a1:yzbx_Ability {id: 'A1', name: '牙周组织解剖识别', category: '基础能力', description: '能够识别和描述正常牙周组织的解剖结构，包括牙龈、牙周膜、牙槽骨和牙骨质', level: 'basic'})
CREATE (a2:yzbx_Ability {id: 'A2', name: '牙周探诊技术', category: '基础能力', description: '掌握正确的牙周探诊方法和技巧，能够准确测量探诊深度', level: 'basic'})
CREATE (a3:yzbx_Ability {id: 'A3', name: '牙菌斑识别', category: '诊断能力', description: '能够识别和评估牙菌斑的分布和程度，理解菌斑染色方法', level: 'intermediate'})
CREATE (a4:yzbx_Ability {id: 'A4', name: '牙周病诊断', category: '诊断能力', description: '能够根据临床表现做出正确的牙周病诊断，掌握2018年新分类', level: 'intermediate'})
CREATE (a5:yzbx_Ability {id: 'A5', name: 'X线片解读', category: '诊断能力', description: '能够解读牙周病相关的X线影像，判断骨吸收类型和程度', level: 'intermediate'})
CREATE (a6:yzbx_Ability {id: 'A6', name: '洁治术操作', category: '治疗能力', description: '掌握龈上洁治术的操作技能，熟悉超声和手工器械使用', level: 'intermediate'})
CREATE (a7:yzbx_Ability {id: 'A7', name: '刮治术操作', category: '治疗能力', description: '掌握龈下刮治和根面平整术的操作要点', level: 'advanced'})
CREATE (a8:yzbx_Ability {id: 'A8', name: '治疗计划制定', category: '治疗能力', description: '能够制定合理的牙周治疗计划，包括分期分级和预后评估', level: 'advanced'})
CREATE (a9:yzbx_Ability {id: 'A9', name: '口腔卫生指导', category: '预防能力', description: '能够进行有效的口腔卫生宣教，指导患者正确刷牙和使用辅助工具', level: 'basic'})
CREATE (a10:yzbx_Ability {id: 'A10', name: '维护治疗管理', category: '预防能力', description: '掌握牙周维护治疗的原则和方法，制定个性化复查计划', level: 'intermediate'})

// ==================== 模块-章节关系 ====================
CREATE (m1)-[:CONTAINS]->(c1_1)
CREATE (m1)-[:CONTAINS]->(c1_2)
CREATE (m2)-[:CONTAINS]->(c2_1)
CREATE (m2)-[:CONTAINS]->(c2_2)
CREATE (m3)-[:CONTAINS]->(c3_1)
CREATE (m3)-[:CONTAINS]->(c3_2)
CREATE (m4)-[:CONTAINS]->(c4_1)
CREATE (m4)-[:CONTAINS]->(c4_2)
CREATE (m5)-[:CONTAINS]->(c5_1)
CREATE (m5)-[:CONTAINS]->(c5_2)

// ==================== 章节-知识点关系 ====================
CREATE (c1_1)-[:CONTAINS]->(k1)
CREATE (c1_1)-[:CONTAINS]->(k2)
CREATE (c1_1)-[:CONTAINS]->(k3)
CREATE (c1_1)-[:CONTAINS]->(k4)
CREATE (c1_2)-[:CONTAINS]->(k5)
CREATE (c1_2)-[:CONTAINS]->(k6)
CREATE (c1_2)-[:CONTAINS]->(k7)
CREATE (c2_1)-[:CONTAINS]->(k8)
CREATE (c2_1)-[:CONTAINS]->(k9)
CREATE (c2_1)-[:CONTAINS]->(k10)
CREATE (c2_2)-[:CONTAINS]->(k11)
CREATE (c2_2)-[:CONTAINS]->(k12)
CREATE (c2_2)-[:CONTAINS]->(k13)
CREATE (c3_1)-[:CONTAINS]->(k14)
CREATE (c3_1)-[:CONTAINS]->(k15)
CREATE (c3_1)-[:CONTAINS]->(k16)
CREATE (c3_2)-[:CONTAINS]->(k17)
CREATE (c3_2)-[:CONTAINS]->(k18)
CREATE (c3_2)-[:CONTAINS]->(k19)
CREATE (c4_1)-[:CONTAINS]->(k20)
CREATE (c4_1)-[:CONTAINS]->(k21)
CREATE (c4_1)-[:CONTAINS]->(k22)
CREATE (c4_2)-[:CONTAINS]->(k23)
CREATE (c4_2)-[:CONTAINS]->(k24)
CREATE (c4_2)-[:CONTAINS]->(k25)
CREATE (c5_1)-[:CONTAINS]->(k26)
CREATE (c5_1)-[:CONTAINS]->(k27)
CREATE (c5_1)-[:CONTAINS]->(k28)
CREATE (c5_2)-[:CONTAINS]->(k29)
CREATE (c5_2)-[:CONTAINS]->(k30)
CREATE (c5_2)-[:CONTAINS]->(k31)

// ==================== 知识点关联关系 ====================
CREATE (k1)-[:RELATES_TO {type: '产生'}]->(k5)
CREATE (k2)-[:RELATES_TO {type: '决定'}]->(k6)
CREATE (k3)-[:RELATES_TO {type: '遵循'}]->(k7)
CREATE (k8)-[:RELATES_TO {type: '涉及'}]->(k9)
CREATE (k8)-[:RELATES_TO {type: '导致'}]->(k11)
CREATE (k9)-[:RELATES_TO {type: '构成'}]->(k10)
CREATE (k14)-[:RELATES_TO {type: '用于'}]->(k15)
CREATE (k18)-[:RELATES_TO {type: '依据'}]->(k19)
CREATE (k20)-[:PREREQUISITE]->(k21)
CREATE (k21)-[:PREREQUISITE]->(k22)
CREATE (k23)-[:RELATES_TO {type: '结合'}]->(k24)
CREATE (k27)-[:RELATES_TO {type: '包含'}]->(k26)
CREATE (k30)-[:RELATES_TO {type: '规定'}]->(k29)
CREATE (k9)-[:RELATES_TO {type: '指导'}]->(k14)
CREATE (k7)-[:RELATES_TO {type: '原理'}]->(k24)
CREATE (k5)-[:RELATES_TO {type: '评估'}]->(k14)

// ==================== 能力-知识点关系 ====================
CREATE (a1)-[:REQUIRES {weight: 0.9}]->(k1)
CREATE (a1)-[:REQUIRES {weight: 0.9}]->(k2)
CREATE (a1)-[:REQUIRES {weight: 0.8}]->(k3)
CREATE (a1)-[:REQUIRES {weight: 0.7}]->(k4)
CREATE (a2)-[:REQUIRES {weight: 0.9}]->(k8)
CREATE (a2)-[:REQUIRES {weight: 0.9}]->(k9)
CREATE (a2)-[:REQUIRES {weight: 0.8}]->(k10)
CREATE (a2)-[:REQUIRES {weight: 0.7}]->(k11)
CREATE (a3)-[:REQUIRES {weight: 0.9}]->(k14)
CREATE (a3)-[:REQUIRES {weight: 0.9}]->(k15)
CREATE (a3)-[:REQUIRES {weight: 0.8}]->(k16)
CREATE (a4)-[:REQUIRES {weight: 0.9}]->(k17)
CREATE (a4)-[:REQUIRES {weight: 0.9}]->(k18)
CREATE (a4)-[:REQUIRES {weight: 0.9}]->(k19)
CREATE (a5)-[:REQUIRES {weight: 0.8}]->(k17)
CREATE (a5)-[:REQUIRES {weight: 0.9}]->(k18)
CREATE (a5)-[:REQUIRES {weight: 0.9}]->(k19)
CREATE (a6)-[:REQUIRES {weight: 0.9}]->(k20)
CREATE (a6)-[:REQUIRES {weight: 0.9}]->(k21)
CREATE (a6)-[:REQUIRES {weight: 0.8}]->(k22)
CREATE (a7)-[:REQUIRES {weight: 0.9}]->(k26)
CREATE (a7)-[:REQUIRES {weight: 0.9}]->(k27)
CREATE (a7)-[:REQUIRES {weight: 0.7}]->(k28)

// ==================== 模块顺序关系 ====================
CREATE (m1)-[:NEXT]->(m2)
CREATE (m2)-[:NEXT]->(m3)
CREATE (m3)-[:NEXT]->(m4)
CREATE (m4)-[:NEXT]->(m5)
