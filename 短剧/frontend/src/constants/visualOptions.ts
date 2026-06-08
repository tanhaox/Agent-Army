/**
 * 视觉设定选项常量 - 专业级短剧视觉风格选项库。
 *
 * 每个选项包含：label（显示名）、value（存储值）、group（分组）、description（悬浮描述）。
 * 按 n-select 的 SelectOption 格式导出，支持分组显示。
 */

export interface VisualOption {
  label: string
  value: string
  group: string
  description: string
}

// ==================== 画风 ====================

export const ART_STYLE_OPTIONS: VisualOption[] = [
  // --- 国风/东方 ---
  { label: '水墨风', value: '水墨风', group: '国风/东方', description: '传统水墨渲染，意境深远，留白与墨韵' },
  { label: '工笔重彩', value: '工笔重彩', group: '国风/东方', description: '工整细腻，色彩浓郁，宫廷画风' },
  { label: '敦煌壁画风', value: '敦煌壁画风', group: '国风/东方', description: '仿敦煌莫高窟壁画，矿物颜料质感' },
  { label: '浮世绘风', value: '浮世绘风', group: '国风/东方', description: '日本浮世绘版画风格，平面装饰感' },
  { label: '国画写意', value: '国画写意', group: '国风/东方', description: '大写意花鸟山水，笔墨豪放' },
  { label: '年画风', value: '年画风', group: '国风/东方', description: '中国民间年画，喜庆浓烈色彩' },
  { label: '青绿山水', value: '青绿山水', group: '国风/东方', description: '石青石绿为主色调的古典山水' },
  { label: '白描风', value: '白描风', group: '国风/东方', description: '纯线条勾勒，不加渲染' },
  { label: '绢本质感', value: '绢本质感', group: '国风/东方', description: '仿古绢本画作，温润如玉' },
  { label: '唐卡风', value: '唐卡风', group: '国风/东方', description: '藏传佛教唐卡风格，金线描边' },
  // --- 二次元/漫画 ---
  { label: '日系动漫', value: '日系动漫', group: '二次元/漫画', description: '经典日式动画风格，大眼萌系' },
  { label: '赛璐璐', value: '赛璐璐', group: '二次元/漫画', description: '平涂上色，色块分明，复古动画感' },
  { label: '韩系插画', value: '韩系插画', group: '二次元/漫画', description: '韩国网漫/游戏立绘风格，精致唯美' },
  { label: '国漫风', value: '国漫风', group: '二次元/漫画', description: '中国动画风格，如《哪吒》《白蛇》' },
  { label: '美漫风', value: '美漫风', group: '二次元/漫画', description: '美式超级英雄漫画，粗犷线条' },
  { label: 'Q版萌系', value: 'Q版萌系', group: '二次元/漫画', description: '超可爱Q版，大头小身体' },
  { label: '像素风', value: '像素风', group: '二次元/漫画', description: '复古像素画风格，8-bit/16-bit' },
  { label: '漫画网点', value: '漫画网点', group: '二次元/漫画', description: '黑白漫画网点纸效果' },
  { label: '厚涂二次元', value: '厚涂二次元', group: '二次元/漫画', description: '二次元造型+厚涂质感，介于动漫与写实' },
  { label: '绘本风', value: '绘本风', group: '二次元/漫画', description: '儿童绘本风格，温暖柔和' },
  // --- 写实/摄影 ---
  { label: '照片写实', value: '照片写实', group: '写实/摄影', description: '超写实照片级渲染，以假乱真' },
  { label: '电影剧照', value: '电影剧照', group: '写实/摄影', description: '电影画面质感，宽画幅构图' },
  { label: '胶片摄影', value: '胶片摄影', group: '写实/摄影', description: '模拟胶片颗粒和色调偏移' },
  { label: '宝丽来', value: '宝丽来', group: '写实/摄影', description: '即时成像照片风格，复古褪色' },
  { label: '半写实', value: '半写实', group: '写实/摄影', description: '写实与风格化之间，适度美化' },
  { label: '杂志时尚', value: '杂志时尚', group: '写实/摄影', description: '时尚杂志封面风格，精致修图' },
  { label: '纪实摄影', value: '纪实摄影', group: '写实/摄影', description: '新闻纪实风格，真实自然' },
  { label: '黑白摄影', value: '黑白摄影', group: '写实/摄影', description: '经典黑白照片，高对比银盐质感' },
  { label: '复古色调', value: '复古色调', group: '写实/摄影', description: '80/90年代老照片色调，泛黄怀旧' },
  { label: '柔焦人像', value: '柔焦人像', group: '写实/摄影', description: '柔焦镜头人像，梦幻朦胧美' },
  // --- 奇幻/科幻 ---
  { label: '暗黑奇幻', value: '暗黑奇幻', group: '奇幻/科幻', description: '哥特暗黑风，恐怖美学' },
  { label: '赛博朋克', value: '赛博朋克', group: '奇幻/科幻', description: '霓虹与机械，高科技低生活' },
  { label: '蒸汽朋克', value: '蒸汽朋克', group: '奇幻/科幻', description: '维多利亚时代蒸汽机械美学' },
  { label: '太空歌剧', value: '太空歌剧', group: '奇幻/科幻', description: '宏大太空场景，星际史诗' },
  { label: '末世废土', value: '末世废土', group: '奇幻/科幻', description: '文明崩塌后的荒芜世界' },
  { label: '仙侠玄幻', value: '仙侠玄幻', group: '奇幻/科幻', description: '修仙世界，灵气飞剑，空灵飘逸' },
  { label: '克苏鲁', value: '克苏鲁', group: '奇幻/科幻', description: '洛夫克拉夫特式恐怖，触手异形' },
  { label: '柴油朋克', value: '柴油朋克', group: '奇幻/科幻', description: '一战后工业化粗犷机械风' },
  { label: '生物朋克', value: '生物朋克', group: '奇幻/科幻', description: '生物科技变异，有机与机械融合' },
  { label: '太阳朋克', value: '太阳朋克', group: '奇幻/科幻', description: '理想化绿色未来，自然与科技共生' },
  // --- 抽象/艺术 ---
  { label: '油画风', value: '油画风', group: '抽象/艺术', description: '经典油画笔触，厚涂质感' },
  { label: '水彩风', value: '水彩风', group: '抽象/艺术', description: '透明水彩渲染，自然晕染' },
  { label: '波普艺术', value: '波普艺术', group: '抽象/艺术', description: '安迪·沃霍尔风格，鲜艳色块重复' },
  { label: '极简主义', value: '极简主义', group: '抽象/艺术', description: '少即是多，大留白简洁线条' },
  { label: '超现实主义', value: '超现实主义', group: '抽象/艺术', description: '达利/马格利特式梦境画面' },
  { label: '印象派', value: '印象派', group: '抽象/艺术', description: '莫奈式光影斑驳，色彩朦胧' },
  { label: '色块拼贴', value: '色块拼贴', group: '抽象/艺术', description: '蒙德里安式几何色块' },
  { label: '素描速写', value: '素描速写', group: '抽象/艺术', description: '铅笔素描风格，线条感强' },
  { label: '蜡笔画', value: '蜡笔画', group: '抽象/艺术', description: '儿童蜡笔质感，天真拙朴' },
  { label: '剪纸风', value: '剪纸风', group: '抽象/艺术', description: '中国民间剪纸/皮影戏风格' },
]

// ==================== 时代 ====================

export const ERA_OPTIONS: VisualOption[] = [
  // --- 远古神话 ---
  { label: '盘古开天', value: '盘古开天', group: '远古神话', description: '天地初开，混沌未分' },
  { label: '三皇五帝', value: '三皇五帝', group: '远古神话', description: '上古部落联盟时代' },
  { label: '封神演义', value: '封神演义', group: '远古神话', description: '商周之际神魔大战' },
  { label: '山海经', value: '山海经', group: '远古神话', description: '上古异兽神话世界' },
  { label: '女娲补天', value: '女娲补天', group: '远古神话', description: '远古创世神话' },
  { label: '希腊神话', value: '希腊神话', group: '远古神话', description: '奥林匹斯众神时代' },
  { label: '北欧神话', value: '北欧神话', group: '远古神话', description: '诸神黄昏前的阿斯加德' },
  { label: '埃及法老', value: '埃及法老', group: '远古神话', description: '金字塔与尼罗河的黄金时代' },
  { label: '亚特兰蒂斯', value: '亚特兰蒂斯', group: '远古神话', description: '传说中的海底文明' },
  { label: '洪荒时代', value: '洪荒时代', group: '远古神话', description: '天地初辟，万物生长' },
  // --- 封建王朝 ---
  { label: '春秋战国', value: '春秋战国', group: '封建王朝', description: '百家争鸣，诸侯争霸' },
  { label: '秦朝', value: '秦朝', group: '封建王朝', description: '大一统帝国，兵马俑' },
  { label: '汉朝', value: '汉朝', group: '封建王朝', description: '丝绸之路，汉武盛世' },
  { label: '三国', value: '三国', group: '封建王朝', description: '魏蜀吴三足鼎立' },
  { label: '魏晋南北朝', value: '魏晋南北朝', group: '封建王朝', description: '竹林七贤，玄学清谈' },
  { label: '隋唐', value: '隋唐', group: '封建王朝', description: '开元盛世，万国来朝' },
  { label: '宋朝', value: '宋朝', group: '封建王朝', description: '文化鼎盛，清明上河图' },
  { label: '元朝', value: '元朝', group: '封建王朝', description: '蒙古帝国，草原铁骑' },
  { label: '明朝', value: '明朝', group: '封建王朝', description: '紫禁城，郑和下西洋' },
  { label: '清朝', value: '清朝', group: '封建王朝', description: '康乾盛世，晚清衰落' },
  { label: '中世纪', value: '中世纪', group: '封建王朝', description: '欧洲骑士与城堡' },
  { label: '维多利亚', value: '维多利亚', group: '封建王朝', description: '英国维多利亚时代' },
  // --- 近现代 ---
  { label: '民国', value: '民国', group: '近现代', description: '旗袍长衫，十里洋场' },
  { label: '抗战年代', value: '抗战年代', group: '近现代', description: '烽火岁月，民族存亡' },
  { label: '新中国初期', value: '新中国初期', group: '近现代', description: '50-60年代新中国建设' },
  { label: '改革开放', value: '改革开放', group: '近现代', description: '80-90年代经济腾飞' },
  { label: '千禧年代', value: '千禧年代', group: '近现代', description: '2000年代互联网初期' },
  { label: '现代都市', value: '现代都市', group: '近现代', description: '当代中国城市生活' },
  { label: '校园现代', value: '校园现代', group: '近现代', description: '当代校园青春' },
  { label: '工业革命', value: '工业革命', group: '近现代', description: '蒸汽机与工厂时代' },
  { label: '美国黄金年代', value: '美国黄金年代', group: '近现代', description: '1950s美国战后繁荣' },
  { label: '香港复古', value: '香港复古', group: '近现代', description: '80-90年代港风黄金期' },
  { label: '苏联时代', value: '苏联时代', group: '近现代', description: '苏联美学，红色帝国' },
  { label: '昭和时代', value: '昭和时代', group: '近现代', description: '日本昭和年代怀旧感' },
  // --- 未来科幻 ---
  { label: '近未来', value: '近未来', group: '未来科幻', description: '2030-2050年近未来科技' },
  { label: '赛博时代', value: '赛博时代', group: '未来科幻', description: '脑机接口，意识上传' },
  { label: '太空殖民', value: '太空殖民', group: '未来科幻', description: '火星基地，星际移民' },
  { label: 'AI觉醒', value: 'AI觉醒', group: '未来科幻', description: '人工智能觉醒时代' },
  { label: '后人类', value: '后人类', group: '未来科幻', description: '基因改造，机械飞升' },
  { label: '银河帝国', value: '银河帝国', group: '未来科幻', description: '星际文明帝国时代' },
  { label: '量子时代', value: '量子时代', group: '未来科幻', description: '量子计算普及的未来' },
  { label: '时间旅行', value: '时间旅行', group: '未来科幻', description: '跨时代时间线交错' },
  { label: '虚拟现实', value: '虚拟现实', group: '未来科幻', description: '元宇宙与虚拟世界' },
  { label: '生化危机', value: '生化危机', group: '未来科幻', description: '病毒肆虐，人类存亡' },
  { label: '末日废土', value: '末日废土', group: '未来科幻', description: '核战后荒芜废土世界' },
  { label: '机甲时代', value: '机甲时代', group: '未来科幻', description: '巨型机甲战斗时代' },
  // --- 架空幻想 ---
  { label: '修仙世界', value: '修仙世界', group: '架空幻想', description: '灵气修炼，飞升成仙' },
  { label: '魔法学院', value: '魔法学院', group: '架空幻想', description: '魔法师培训学院' },
  { label: '精灵森林', value: '精灵森林', group: '架空幻想', description: '精灵族的自然王国' },
  { label: '矮人王国', value: '矮人王国', group: '架空幻想', description: '地下矿洞矮人工匠文明' },
  { label: '龙族纪元', value: '龙族纪元', group: '架空幻想', description: '巨龙统治的奇幻世界' },
  { label: '暗夜领主', value: '暗夜领主', group: '架空幻想', description: '吸血鬼暗夜王国' },
  { label: '异世界转生', value: '异世界转生', group: '架空幻想', description: '穿越到奇幻世界的冒险' },
  { label: '梦境世界', value: '梦境世界', group: '架空幻想', description: '超现实梦境空间' },
  { label: '平行宇宙', value: '平行宇宙', group: '架空幻想', description: '多元宇宙的交错碰撞' },
  { label: '灵异世界', value: '灵异世界', group: '架空幻想', description: '鬼怪神灵的幽冥世界' },
  { label: '武侠江湖', value: '武侠江湖', group: '架空幻想', description: '刀光剑影，快意恩仇' },
  { label: '西游世界', value: '西游世界', group: '架空幻想', description: '取经路上的妖魔鬼怪' },
]

// ==================== 环境 ====================

export const ENVIRONMENT_OPTIONS: VisualOption[] = [
  // --- 城市 ---
  { label: '繁华商业街', value: '繁华商业街', group: '城市', description: '霓虹灯与广告牌的繁忙街道' },
  { label: '老旧巷弄', value: '老旧巷弄', group: '城市', description: '斑驳墙面的市井小巷' },
  { label: '现代办公室', value: '现代办公室', group: '城市', description: '高层写字楼，落地窗城市天际线' },
  { label: '豪华公寓', value: '豪华公寓', group: '城市', description: '高端住宅，城市夜景阳台' },
  { label: '地下停车场', value: '地下停车场', group: '城市', description: '昏暗灯光的水泥空间' },
  { label: '天台', value: '天台', group: '城市', description: '楼顶天台，俯瞰城市灯火' },
  { label: '地铁车厢', value: '地铁车厢', group: '城市', description: '拥挤或空旷的地铁空间' },
  { label: '夜市', value: '夜市', group: '城市', description: '烟火气十足的夜市小吃街' },
  { label: '废弃工厂', value: '废弃工厂', group: '城市', description: '锈蚀机器与破碎玻璃' },
  { label: '港口码头', value: '港口码头', group: '城市', description: '集装箱与起重机，海风咸腥' },
  { label: '医院走廊', value: '医院走廊', group: '城市', description: '白色灯光的消毒走廊' },
  // --- 自然 ---
  { label: '竹林深处', value: '竹林深处', group: '自然', description: '幽静竹林，光影斑驳' },
  { label: '海边悬崖', value: '海边悬崖', group: '自然', description: '波涛拍岸的峭壁' },
  { label: '雪山之巅', value: '雪山之巅', group: '自然', description: '皑皑白雪，万里无云' },
  { label: '沙漠绿洲', value: '沙漠绿洲', group: '自然', description: '黄沙中的生命绿洲' },
  { label: '热带雨林', value: '热带雨林', group: '自然', description: '茂密植被，藤蔓缠绕' },
  { label: '樱花大道', value: '樱花大道', group: '自然', description: '粉色花瓣纷飞的长道' },
  { label: '瀑布深潭', value: '瀑布深潭', group: '自然', description: '飞流直下，碧水幽潭' },
  { label: '草原牧场', value: '草原牧场', group: '自然', description: '一望无际的绿色草原' },
  { label: '秋日枫林', value: '秋日枫林', group: '自然', description: '红叶漫天的金色秋天' },
  { label: '月下湖面', value: '月下湖面', group: '自然', description: '月光如镜的宁静湖面' },
  // --- 奇幻 ---
  { label: '浮空仙岛', value: '浮空仙岛', group: '奇幻', description: '云海之上的悬浮仙山' },
  { label: '龙穴宝藏', value: '龙穴宝藏', group: '奇幻', description: '巨龙守护的宝石洞穴' },
  { label: '魔法图书馆', value: '魔法图书馆', group: '奇幻', description: '漂浮书籍的魔法空间' },
  { label: '精灵树城', value: '精灵树城', group: '奇幻', description: '参天巨树中的精灵城市' },
  { label: '暗黑地下城', value: '暗黑地下城', group: '奇幻', description: '迷宫般的地下世界' },
  { label: '天空之城', value: '天空之城', group: '奇幻', description: '云端之上的漂浮城邦' },
  { label: '水晶洞穴', value: '水晶洞穴', group: '奇幻', description: '发光水晶的地下空间' },
  { label: '魔法森林', value: '魔法森林', group: '奇幻', description: '会发光的奇异植物' },
  { label: '冥界入口', value: '冥界入口', group: '奇幻', description: '通往幽冥世界的传送门' },
  { label: '火山祭坛', value: '火山祭坛', group: '奇幻', description: '岩浆环绕的古代祭坛' },
  // --- 科幻 ---
  { label: '太空站', value: '太空站', group: '科幻', description: '零重力太空站内部' },
  { label: '赛博街道', value: '赛博街道', group: '科幻', description: '全息广告与霓虹的雨夜街道' },
  { label: '虚拟矩阵', value: '虚拟矩阵', group: '科幻', description: '数字化的虚拟世界空间' },
  { label: '机甲仓库', value: '机甲仓库', group: '科幻', description: '巨型机甲维修基地' },
  { label: '冷冻休眠舱', value: '冷冻休眠舱', group: '科幻', description: '星际飞船的冷冻休眠区' },
  { label: '量子实验室', value: '量子实验室', group: '科幻', description: '尖端科技的量子研究设施' },
  { label: '克隆工厂', value: '克隆工厂', group: '科幻', description: '生物培养皿的克隆设施' },
  { label: '太空电梯', value: '太空电梯', group: '科幻', description: '连接地球与太空的巨型电梯' },
  { label: '火星基地', value: '火星基地', group: '科幻', description: '红色星球上的人类定居点' },
  { label: '废墟城市', value: '废墟城市', group: '科幻', description: '文明崩塌后的城市残骸' },
  // --- 历史 ---
  { label: '古代宫殿', value: '古代宫殿', group: '历史', description: '金碧辉煌的皇家宫殿' },
  { label: '古战场', value: '古战场', group: '历史', description: '旌旗飘扬的古代战场' },
  { label: '古代客栈', value: '古代客栈', group: '历史', description: '江湖气息的龙门客栈' },
  { label: '皇家园林', value: '皇家园林', group: '历史', description: '亭台楼阁，小桥流水' },
  { label: '古城门楼', value: '古城门楼', group: '历史', description: '巍峨的城门与城墙' },
  { label: '古代集市', value: '古代集市', group: '历史', description: '热闹非凡的古代坊市' },
  { label: '寺庙大殿', value: '寺庙大殿', group: '历史', description: '香烟缭绕的古刹大雄宝殿' },
  { label: '水乡古镇', value: '水乡古镇', group: '历史', description: '小桥流水人家，乌篷船' },
  { label: '中世纪城堡', value: '中世纪城堡', group: '历史', description: '石砌城堡，护城河环绕' },
  { label: '古埃及神庙', value: '古埃及神庙', group: '历史', description: '巨大石柱与壁画的神殿' },
  // --- 恐怖 ---
  { label: '废弃医院', value: '废弃医院', group: '恐怖', description: '空荡恐怖的废弃精神病院' },
  { label: '雾中墓地', value: '雾中墓地', group: '恐怖', description: '浓雾弥漫的古老墓园' },
  { label: '镜中世界', value: '镜中世界', group: '恐怖', description: '镜子里的诡异镜像空间' },
  { label: '血月之夜', value: '血月之夜', group: '恐怖', description: '血红色月亮笼罩的诡异夜晚' },
  { label: '幽暗地下室', value: '幽暗地下室', group: '恐怖', description: '潮湿阴暗的地下空间' },
  { label: '鬼屋走廊', value: '鬼屋走廊', group: '恐怖', description: '布满蛛网的幽长走廊' },
  { label: '寂静湖泊', value: '寂静湖泊', group: '恐怖', description: '雾气笼罩的死寂湖面' },
  { label: '枯木林', value: '枯木林', group: '恐怖', description: '扭曲枯树的无叶森林' },
]

// ==================== 色调 ====================

export const COLOR_PALETTE_OPTIONS: VisualOption[] = [
  // --- 冷色调 ---
  { label: '冰蓝', value: '冰蓝', group: '冷色调', description: '清澈透明的冰蓝色调' },
  { label: '深海蓝', value: '深海蓝', group: '冷色调', description: '深邃神秘的海蓝色调' },
  { label: '极光绿', value: '极光绿', group: '冷色调', description: '北极光般的翠绿光辉' },
  { label: '银灰', value: '银灰', group: '冷色调', description: '冷静理性的银灰色调' },
  { label: '薄荷冷绿', value: '薄荷冷绿', group: '冷色调', description: '清凉的薄荷绿色调' },
  { label: '星空靛蓝', value: '星空靛蓝', group: '冷色调', description: '深邃夜空的靛蓝色调' },
  { label: '冰川白蓝', value: '冰川白蓝', group: '冷色调', description: '冰川反射的淡蓝白色调' },
  { label: '紫罗兰', value: '紫罗兰', group: '冷色调', description: '优雅神秘的紫罗兰色调' },
  { label: '青瓷色', value: '青瓷色', group: '冷色调', description: '宋代青瓷的温润色调' },
  { label: '月光银', value: '月光银', group: '冷色调', description: '月光洒落的银白色调' },
  // --- 暖色调 ---
  { label: '落日橙', value: '落日橙', group: '暖色调', description: '夕阳西下的温暖橙色调' },
  { label: '琥珀金', value: '琥珀金', group: '暖色调', description: '琥珀色的温暖金色调' },
  { label: '玫瑰粉', value: '玫瑰粉', group: '暖色调', description: '浪漫柔和的玫瑰粉色调' },
  { label: '焦糖棕', value: '焦糖棕', group: '暖色调', description: '温暖醇厚的焦糖棕色调' },
  { label: '蜜桃色', value: '蜜桃色', group: '暖色调', description: '甜美可人的蜜桃色调' },
  { label: '暖白奶油', value: '暖白奶油', group: '暖色调', description: '柔和温暖的奶油白色调' },
  { label: '秋叶红棕', value: '秋叶红棕', group: '暖色调', description: '秋天落叶的红棕色调' },
  { label: '烛光黄', value: '烛光黄', group: '暖色调', description: '温暖昏黄的烛光色调' },
  { label: '砖红色', value: '砖红色', group: '暖色调', description: '复古温暖的砖红色调' },
  { label: '朱砂赤', value: '朱砂赤', group: '暖色调', description: '中国传统朱砂红色调' },
  // --- 对比色 ---
  { label: '黑白极简', value: '黑白极简', group: '对比色', description: '纯黑白高对比色调' },
  { label: '红绿撞色', value: '红绿撞色', group: '对比色', description: '大胆的红绿对比色' },
  { label: '紫橙对比', value: '紫橙对比', group: '对比色', description: '赛博朋克经典紫橙色调' },
  { label: '青红互补', value: '青红互补', group: '对比色', description: '电影感的青橙互补色调' },
  { label: '金银辉映', value: '金银辉映', group: '对比色', description: '金色与银色的华丽对比' },
  { label: '蓝橙冷暖', value: '蓝橙冷暖', group: '对比色', description: '冷蓝暖橙的经典冷暖对比' },
  { label: '红黑暗夜', value: '红黑暗夜', group: '对比色', description: '暗黑基调中的血红点缀' },
  { label: '白红圣洁', value: '白红圣洁', group: '对比色', description: '白色基调中的红色点缀' },
  { label: '黑金奢华', value: '黑金奢华', group: '对比色', description: '黑色底上的金色华丽' },
  { label: '霓虹多彩', value: '霓虹多彩', group: '对比色', description: '霓虹灯般的鲜艳多彩' },
  // --- 低饱和 ---
  { label: '灰调莫兰迪', value: '灰调莫兰迪', group: '低饱和', description: '高级灰莫兰迪色系' },
  { label: '雾霾蓝灰', value: '雾霾蓝灰', group: '低饱和', description: '朦胧的雾霾蓝灰色调' },
  { label: '旧照片褪色', value: '旧照片褪色', group: '低饱和', description: '老照片般的褪色低饱和' },
  { label: '枯叶色', value: '枯叶色', group: '低饱和', description: '干枯叶片的暗淡色调' },
  { label: '水泥灰', value: '水泥灰', group: '低饱和', description: '工业风水泥灰色调' },
  { label: '沙漠黄灰', value: '沙漠黄灰', group: '低饱和', description: '沙漠般的黄灰低饱和' },
  { label: '青铜绿', value: '青铜绿', group: '低饱和', description: '氧化青铜的暗绿色调' },
  { label: '烟熏色', value: '烟熏色', group: '低饱和', description: '烟雾弥漫的朦胧色调' },
  { label: '陶土色', value: '陶土色', group: '低饱和', description: '陶器般的灰橙色调' },
  { label: '旧报纸', value: '旧报纸', group: '低饱和', description: '泛黄旧报纸的褐色调' },
  // --- 高饱和 ---
  { label: '荧光绿', value: '荧光绿', group: '高饱和', description: '刺眼的荧光绿色调' },
  { label: '电光蓝', value: '电光蓝', group: '高饱和', description: '强烈明亮的电光蓝' },
  { label: '烈焰红', value: '烈焰红', group: '高饱和', description: '燃烧般的烈焰红色调' },
  { label: '柠檬黄', value: '柠檬黄', group: '高饱和', description: '明亮活泼的柠檬黄色调' },
  { label: '洋红紫', value: '洋红紫', group: '高饱和', description: '浓烈鲜艳的洋红紫色' },
  { label: '糖果色', value: '糖果色', group: '高饱和', description: '甜美多彩的糖果色调' },
  { label: '彩虹渐变', value: '彩虹渐变', group: '高饱和', description: '彩虹般的全色谱渐变' },
  { label: '波普鲜艳', value: '波普鲜艳', group: '高饱和', description: '波普艺术般的鲜艳色彩' },
  { label: '赛博霓虹', value: '赛博霓虹', group: '高饱和', description: '赛博朋克霓虹灯光效果' },
  { label: '宝石色', value: '宝石色', group: '高饱和', description: '红宝石蓝宝石般浓郁的宝石色' },
]

// ==================== 光照 ====================

export const LIGHTING_OPTIONS: VisualOption[] = [
  // --- 自然光 ---
  { label: '黄金时段', value: '黄金时段', group: '自然光', description: '日出/日落时的温暖金色光线' },
  { label: '正午阳光', value: '正午阳光', group: '自然光', description: '正午强烈的顶光，硬朗阴影' },
  { label: '阴天漫射', value: '阴天漫射', group: '自然光', description: '阴天柔和均匀的漫射光' },
  { label: '月光清冷', value: '月光清冷', group: '自然光', description: '清冷银白色的月光' },
  { label: '晨曦微光', value: '晨曦微光', group: '自然光', description: '黎明前柔和的粉蓝光线' },
  { label: '树荫斑驳', value: '树荫斑驳', group: '自然光', description: '阳光穿过树叶的光斑效果' },
  { label: '逆光剪影', value: '逆光剪影', group: '自然光', description: '强逆光形成的剪影效果' },
  { label: '丁达尔光', value: '丁达尔光', group: '自然光', description: '光线穿过雾气的耶稣光效果' },
  { label: '极光照明', value: '极光照明', group: '自然光', description: '北极光般的自然彩色光照' },
  { label: '星光照耀', value: '星光照耀', group: '自然光', description: '星空下的微弱星光照明' },
  // --- 人工光 ---
  { label: '白炽灯暖光', value: '白炽灯暖光', group: '人工光', description: '传统白炽灯的暖黄光线' },
  { label: '荧光灯冷白', value: '荧光灯冷白', group: '人工光', description: '办公室荧光灯的冷白光线' },
  { label: '烛光摇曳', value: '烛光摇曳', group: '人工光', description: '蜡烛火焰的温暖闪烁光' },
  { label: '壁炉火光', value: '壁炉火光', group: '人工光', description: '壁炉中跳动的温暖火焰' },
  { label: '台灯局部', value: '台灯局部', group: '人工光', description: '台灯照亮的局部光圈' },
  { label: '灯笼红光', value: '灯笼红光', group: '人工光', description: '红灯笼的温暖红色光晕' },
  { label: '手电筒聚光', value: '手电筒聚光', group: '人工光', description: '黑暗中手电筒的聚焦光束' },
  { label: '火把照明', value: '火把照明', group: '人工光', description: '古代火把的跳跃火焰光' },
  { label: 'LED冷蓝', value: 'LED冷蓝', group: '人工光', description: 'LED灯的冷蓝色调光线' },
  { label: '篝火暖光', value: '篝火暖光', group: '人工光', description: '夜晚篝火的温暖跳动光' },
  // --- 影视光 ---
  { label: '伦勃朗光', value: '伦勃朗光', group: '影视光', description: '经典三角光，戏剧性人像照明' },
  { label: '蝴蝶光', value: '蝴蝶光', group: '影视光', description: '正上方柔光，鼻下蝴蝶形阴影' },
  { label: '分离光', value: '分离光', group: '影视光', description: '半明半暗，只照亮一半脸' },
  { label: '轮廓光', value: '轮廓光', group: '影视光', description: '从后方打亮头发和肩膀轮廓' },
  { label: '眼神光', value: '眼神光', group: '影视光', description: '在瞳孔中制造亮点的补光' },
  { label: '底光恐怖', value: '底光恐怖', group: '影视光', description: '从下方打光，制造恐怖效果' },
  { label: '顶光压迫', value: '顶光压迫', group: '影视光', description: '正上方强光，眼窝深陷的压迫感' },
  { label: '侧光立体', value: '侧光立体', group: '影视光', description: '90度侧光，强烈明暗对比' },
  { label: '柔光箱', value: '柔光箱', group: '影视光', description: '影棚柔光箱的均匀柔和光' },
  { label: '硬光高反差', value: '硬光高反差', group: '影视光', description: '无柔化的硬光源，锐利阴影' },
  // --- 特效光 ---
  { label: '霓虹紫蓝', value: '霓虹紫蓝', group: '特效光', description: '赛博朋克风格的霓虹辉光' },
  { label: '全息投影光', value: '全息投影光', group: '特效光', description: '蓝白色的全息投影光线' },
  { label: '激光网格', value: '激光网格', group: '特效光', description: '红色激光线交叉的网格光效' },
  { label: '能量光束', value: '能量光束', group: '特效光', description: '超能力释放时的能量光束' },
  { label: '魔法治愈', value: '魔法治愈', group: '特效光', description: '绿色/金色的魔法治愈光线' },
  { label: '暗黑侵蚀', value: '暗黑侵蚀', group: '特效光', description: '紫色/黑色的暗能量腐蚀光' },
  { label: '电弧闪电', value: '电弧闪电', group: '特效光', description: '蓝白色电弧闪电的光效' },
  { label: '灵气光环', value: '灵气光环', group: '特效光', description: '修仙者的灵气外放光环' },
  { label: '数据流光', value: '数据流光', group: '特效光', description: '矩阵/代码瀑布的绿色光效' },
  { label: '传送门光', value: '传送门光', group: '特效光', description: '空间传送门的异色光效' },
  // --- 氛围光 ---
  { label: '烟雾逆光', value: '烟雾逆光', group: '氛围光', description: '烟雾中逆光照射的光线效果' },
  { label: '雨中折射', value: '雨中折射', group: '氛围光', description: '雨水反射的霓虹灯光折射' },
  { label: '百叶窗条光', value: '百叶窗条光', group: '氛围光', description: '百叶窗投射的条纹光影' },
  { label: '水下焦散', value: '水下焦散', group: '氛围光', description: '水面折射的波纹光影效果' },
  { label: '灰尘光束', value: '灰尘光束', group: '氛围光', description: '可见灰尘颗粒飘浮的光束' },
  { label: '玻璃彩光', value: '玻璃彩光', group: '氛围光', description: '彩色玻璃透射的彩色光线' },
  { label: '雾中朦胧', value: '雾中朦胧', group: '氛围光', description: '浓雾中的朦胧散射光' },
  { label: '倒影水光', value: '倒影水光', group: '氛围光', description: '水面上倒映的灯光效果' },
  { label: '光晕漏光', value: '光晕漏光', group: '氛围光', description: '镜头漏光/光晕效果' },
  { label: '体积光雾', value: '体积光雾', group: '氛围光', description: '上帝光束般的体积光效果' },
]

// ==================== 分组辅助函数 ====================

/** 将 VisualOption[] 转换为 Naive UI n-select 支持的分组格式（嵌套 children）。 */
export function toGroupedOptions(options: VisualOption[]) {
  const groupMap = new Map<string, { type: 'group'; label: string; key: string; children: Array<{ label: string; value: string }> }>()

  for (const opt of options) {
    if (!groupMap.has(opt.group)) {
      groupMap.set(opt.group, { type: 'group', label: opt.group, key: opt.group, children: [] })
    }
    groupMap.get(opt.group)!.children.push({ label: opt.label, value: opt.value })
  }

  return [...groupMap.values()]
}

/** 获取所有分组名称（用于统计）。 */
export function getGroups(options: VisualOption[]): string[] {
  return [...new Set(options.map(o => o.group))]
}
