"""
资产配置AI - Asset Allocation AI

战略分析军团核心成员

职责：
1. 大类资产配置建议 - 基于宏观经济和市场环境
2. 多模型资产配置 - 均值方差、风险平价、Black-Litterman、动态配置
3. 资产配置优化 - 根据市场环境动态调整配置比例
4. 风险管理 - 评估组合风险，提供风险提示
5. 配置建议生成 - 生成具体的资产配置方案

核心功能：
- 均值方差模型 (Mean-Variance Model)
- 风险平价模型 (Risk Parity Model)
- Black-Litterman模型
- 动态资产配置模型 (Dynamic Asset Allocation)

资产类别：
- 股票 (Equity)
- 债券 (Bond)
- 现金 (Cash)
- 商品 (Commodity)
- 房地产 (Real Estate)

使用工具：
- MacroEconomicAI (宏观经济分析)
- 其他业务层AI (市场情绪、技术分析、基本面分析等)

依赖：
- numpy (数值计算)
- pandas (数据处理)
- scipy (优化求解)

创建日期: 2026-03-15
版本: v1.0
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin


class MarketEnvironment(str, Enum):
    """市场环境"""
    BULL = "牛市"  # 经济增长，股市上涨
    BEAR = "熊市"  # 经济衰退，股市下跌
    VOLATILE = "震荡市"  # 经济不确定，市场波动


class AllocationModel(str, Enum):
    """配置模型"""
    MEAN_VARIANCE = "均值方差模型"
    RISK_PARITY = "风险平价模型"
    BLACK_LITTERMAN = "Black-Litterman模型"
    DYNAMIC = "动态配置模型"


class AssetClass(str, Enum):
    """资产类别"""
    EQUITY = "equity"  # 股票
    BOND = "bond"  # 债券
    CASH = "cash"  # 现金
    COMMODITY = "commodity"  # 商品
    REAL_ESTATE = "real_estate"  # 房地产


class AssetAllocationAI(BaseAgent, LoggerMixin):
    """
    资产配置AI - 战略分析军团核心成员

    核心能力：
    1. 多模型资产配置 - 支持4种经典配置模型
    2. 宏观环境识别 - 自动识别牛市/熊市/震荡市
    3. 动态配置调整 - 根据市场变化调整配置比例
    4. 风险评估 - 计算组合预期收益、风险和夏普比率
    5. 配置建议 - 生成具体的资产配置方案和调整建议

    使用场景：
    - 投资组合构建 - 为投资者构建最优资产配置
    - 配置再平衡 - 定期调整资产配置比例
    - 风险管理 - 评估和控制组合风险
    - 市场环境应对 - 根据市场变化调整配置策略
    """

    # 默认资产预期收益率（年化）
    DEFAULT_EXPECTED_RETURNS = {
        AssetClass.EQUITY: 0.10,  # 股票 10%
        AssetClass.BOND: 0.05,  # 债券 5%
        AssetClass.CASH: 0.03,  # 现金 3%
        AssetClass.COMMODITY: 0.06,  # 商品 6%
        AssetClass.REAL_ESTATE: 0.07,  # 房地产 7%
    }

    # 默认资产波动率（年化）
    DEFAULT_VOLATILITY = {
        AssetClass.EQUITY: 0.20,  # 股票 20%
        AssetClass.BOND: 0.08,  # 债券 8%
        AssetClass.CASH: 0.01,  # 现金 1%
        AssetClass.COMMODITY: 0.15,  # 商品 15%
        AssetClass.REAL_ESTATE: 0.12,  # 房地产 12%
    }

    # 默认资产相关性矩阵
    DEFAULT_CORRELATION = np.array([
        [1.00, 0.30, 0.10, 0.20, 0.25],  # 股票
        [0.30, 1.00, 0.05, 0.10, 0.15],  # 债券
        [0.10, 0.05, 1.00, 0.00, 0.05],  # 现金
        [0.20, 0.10, 0.00, 1.00, 0.10],  # 商品
        [0.25, 0.15, 0.05, 0.10, 1.00],  # 房地产
    ])

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="资产配置AI",
            role="基于宏观经济和市场环境，提供大类资产配置建议",
            capabilities=[
                AgentCapability(
                    name="mean_variance_allocation",
                    description="均值方差模型资产配置",
                    input_schema={
                        "risk_tolerance": "风险容忍度 (0-1, 默认0.5)",
                        "risk_free_rate": "无风险收益率 (默认0.03)"
                    },
                    output_type="asset_allocation_plan"
                ),
                AgentCapability(
                    name="risk_parity_allocation",
                    description="风险平价模型资产配置",
                    input_schema={
                        "risk_budget": "风险预算 (默认等风险)"
                    },
                    output_type="asset_allocation_plan"
                ),
                AgentCapability(
                    name="black_litterman_allocation",
                    description="Black-Litterman模型资产配置",
                    input_schema={
                        "views": "投资者观点",
                        "confidence": "观点置信度"
                    },
                    output_type="asset_allocation_plan"
                ),
                AgentCapability(
                    name="dynamic_allocation",
                    description="动态资产配置",
                    input_schema={
                        "market_environment": "市场环境 (牛市/熊市/震荡市)",
                        "current_allocation": "当前配置"
                    },
                    output_type="asset_allocation_plan"
                ),
                AgentCapability(
                    name="comprehensive_allocation",
                    description="综合资产配置（多模型对比）",
                    input_schema={
                        "risk_tolerance": "风险容忍度",
                        "market_environment": "市场环境"
                    },
                    output_type="comprehensive_allocation_report"
                )
            ],
            tools=[
                AgentTool(
                    name="MacroEconomicAI",
                    description="宏观经济分析工具",
                    required_params=["time_range"]
                )
            ],
            config=config
        )

        # 初始化资产数据
        self.assets = list(AssetClass)
        self.asset_names = {asset: asset.value for asset in self.assets}

        # 计算协方差矩阵
        self.covariance_matrix = self._calculate_covariance_matrix()

        self.logger.info("资产配置AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "allocate":
            return await self.analyze(**kwargs)
        elif task == "mean_variance":
            return await self.mean_variance_allocation(**kwargs)
        elif task == "risk_parity":
            return await self.risk_parity_allocation(**kwargs)
        elif task == "black_litterman":
            return await self.black_litterman_allocation(**kwargs)
        elif task == "dynamic":
            return await self.dynamic_allocation(**kwargs)
        elif task == "comprehensive":
            return await self.comprehensive_allocation(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    async def analyze(
        self,
        model: str = AllocationModel.MEAN_VARIANCE,
        risk_tolerance: float = 0.5,
        market_environment: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        资产配置分析（主入口）

        Args:
            model: 配置模型 (mean_variance/risk_parity/black_litterman/dynamic)
            risk_tolerance: 风险容忍度 (0-1, 0保守, 1激进)
            market_environment: 市场环境 (牛市/熊市/震荡市)
            **kwargs: 其他参数

        Returns:
            资产配置建议:
            {
                "allocation_date": str,
                "model_used": str,
                "macro_environment": str,
                "allocation": {...},
                "portfolio_metrics": {...},
                "adjustment_suggestions": [...],
                "risk_warnings": [...]
            }
        """
        self.logger.info(
            f"开始资产配置分析",
            extra={
                "model": model,
                "risk_tolerance": risk_tolerance,
                "market_environment": market_environment
            }
        )

        try:
            # 1. 识别市场环境（如果未提供）
            if market_environment is None:
                market_environment = await self._identify_market_environment()

            # 2. 根据模型选择配置方法
            if model == AllocationModel.MEAN_VARIANCE:
                allocation_result = await self.mean_variance_allocation(
                    risk_tolerance=risk_tolerance,
                    **kwargs
                )
            elif model == AllocationModel.RISK_PARITY:
                allocation_result = await self.risk_parity_allocation(**kwargs)
            elif model == AllocationModel.BLACK_LITTERMAN:
                allocation_result = await self.black_litterman_allocation(**kwargs)
            elif model == AllocationModel.DYNAMIC:
                allocation_result = await self.dynamic_allocation(
                    market_environment=market_environment,
                    **kwargs
                )
            else:
                raise ValueError(f"未知模型: {model}")

            # 3. 添加市场环境信息
            allocation_result['macro_environment'] = market_environment
            allocation_result['allocation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 4. 生成调整建议
            allocation_result['adjustment_suggestions'] = self._generate_adjustment_suggestions(
                allocation_result
            )

            # 5. 生成风险提示
            allocation_result['risk_warnings'] = self._generate_risk_warnings(
                allocation_result
            )

            self.logger.info(
                f"资产配置分析完成",
                extra={
                    "model": model,
                    "expected_return": allocation_result['portfolio_metrics']['expected_return'],
                    "expected_risk": allocation_result['portfolio_metrics']['expected_risk']
                }
            )

            return allocation_result

        except Exception as e:
            self.logger.error(f"资产配置分析失败: {e}", exc_info=True)
            raise

    async def mean_variance_allocation(
        self,
        risk_tolerance: float = 0.5,
        risk_free_rate: float = 0.03
    ) -> Dict[str, Any]:
        """
        均值方差模型 (Mean-Variance Model)

        经典的马科维茨均值方差模型，在给定风险水平下最大化预期收益

        Args:
            risk_tolerance: 风险容忍度 (0-1)
            risk_free_rate: 无风险收益率

        Returns:
            资产配置结果
        """
        self.logger.info(f"使用均值方差模型进行资产配置", extra={"risk_tolerance": risk_tolerance})

        # 1. 计算预期收益率和协方差矩阵
        expected_returns = np.array([
            self.DEFAULT_EXPECTED_RETURNS[asset] for asset in self.assets
        ])

        # 2. 根据风险容忍度调整目标
        # 保守投资者：最小化风险
        # 激进投资者：最大化收益
        if risk_tolerance < 0.3:
            # 保守：最小化风险
            weights = self._optimize_min_risk(expected_returns, self.covariance_matrix)
        elif risk_tolerance > 0.7:
            # 激进：最大化收益
            weights = self._optimize_max_return(expected_returns, self.covariance_matrix)
        else:
            # 中性：最大化夏普比率
            weights = self._optimize_max_sharpe(
                expected_returns, self.covariance_matrix, risk_free_rate
            )

        # 3. 计算组合指标
        portfolio_metrics = self._calculate_portfolio_metrics(weights, expected_returns)

        # 4. 生成配置结果
        allocation = self._format_allocation_result(weights, expected_returns, portfolio_metrics)

        allocation['model_used'] = AllocationModel.MEAN_VARIANCE

        return allocation

    async def risk_parity_allocation(
        self,
        risk_budget: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        风险平价模型 (Risk Parity Model)

        让每个资产对组合风险的贡献相等（或按指定比例）

        Args:
            risk_budget: 风险预算（默认等风险）

        Returns:
            资产配置结果
        """
        self.logger.info(f"使用风险平价模型进行资产配置")

        # 1. 设置风险预算（默认等风险）
        if risk_budget is None:
            risk_budget = {asset.value: 1.0 / len(self.assets) for asset in self.assets}

        # 2. 优化权重使得风险贡献等于风险预算
        weights = self._optimize_risk_parity(self.covariance_matrix, risk_budget)

        # 3. 计算预期收益率
        expected_returns = np.array([
            self.DEFAULT_EXPECTED_RETURNS[asset] for asset in self.assets
        ])

        # 4. 计算组合指标
        portfolio_metrics = self._calculate_portfolio_metrics(weights, expected_returns)

        # 5. 生成配置结果
        allocation = self._format_allocation_result(weights, expected_returns, portfolio_metrics)

        allocation['model_used'] = AllocationModel.RISK_PARITY

        return allocation

    async def black_litterman_allocation(
        self,
        views: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        Black-Litterman模型

        结合市场均衡和投资者观点，生成更稳定的配置建议

        Args:
            views: 投资者观点列表
            confidence: 观点置信度 (0-1)

        Returns:
            资产配置结果
        """
        self.logger.info(f"使用Black-Litterman模型进行资产配置")

        # 1. 计算市场均衡收益（使用CAPM）
        expected_returns = np.array([
            self.DEFAULT_EXPECTED_RETURNS[asset] for asset in self.assets
        ])

        # 2. 如果有投资者观点，调整预期收益
        if views:
            expected_returns = self._apply_black_litterman_views(
                expected_returns,
                self.covariance_matrix,
                views,
                confidence
            )

        # 3. 最大化夏普比率
        weights = self._optimize_max_sharpe(expected_returns, self.covariance_matrix, 0.03)

        # 4. 计算组合指标
        portfolio_metrics = self._calculate_portfolio_metrics(weights, expected_returns)

        # 5. 生成配置结果
        allocation = self._format_allocation_result(weights, expected_returns, portfolio_metrics)

        allocation['model_used'] = AllocationModel.BLACK_LITTERMAN

        return allocation

    async def dynamic_allocation(
        self,
        market_environment: str = MarketEnvironment.VOLATILE,
        current_allocation: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        动态资产配置模型 (Dynamic Asset Allocation)

        根据市场环境动态调整资产配置比例

        Args:
            market_environment: 市场环境 (牛市/熊市/震荡市)
            current_allocation: 当前配置（用于生成调整建议）

        Returns:
            资产配置结果
        """
        self.logger.info(
            f"使用动态配置模型进行资产配置",
            extra={"market_environment": market_environment}
        )

        # 1. 根据市场环境确定目标配置
        target_allocation = self._get_target_allocation_by_environment(market_environment)

        # 2. 计算预期收益率和组合指标
        expected_returns = np.array([
            self.DEFAULT_EXPECTED_RETURNS[asset] for asset in self.assets
        ])

        weights = np.array([target_allocation[asset.value] for asset in self.assets])

        # 3. 计算组合指标
        portfolio_metrics = self._calculate_portfolio_metrics(weights, expected_returns)

        # 4. 生成配置结果
        allocation = self._format_allocation_result(weights, expected_returns, portfolio_metrics)

        allocation['model_used'] = AllocationModel.DYNAMIC

        # 5. 如果有当前配置，生成调整建议
        if current_allocation:
            allocation['current_allocation'] = current_allocation

        return allocation

    async def comprehensive_allocation(
        self,
        risk_tolerance: float = 0.5,
        market_environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        综合资产配置（多模型对比）

        使用所有4种模型进行配置，并对比分析

        Args:
            risk_tolerance: 风险容忍度
            market_environment: 市场环境

        Returns:
            综合配置报告
        """
        self.logger.info(f"执行综合资产配置分析")

        # 1. 识别市场环境
        if market_environment is None:
            market_environment = await self._identify_market_environment()

        # 2. 运行所有4种模型
        models_results = {}

        models_results['mean_variance'] = await self.mean_variance_allocation(
            risk_tolerance=risk_tolerance
        )

        models_results['risk_parity'] = await self.risk_parity_allocation()

        models_results['black_litterman'] = await self.black_litterman_allocation()

        models_results['dynamic'] = await self.dynamic_allocation(
            market_environment=market_environment
        )

        # 3. 对比分析
        comparison = self._compare_models(models_results)

        # 4. 推荐最优模型
        recommended_model = self._recommend_model(comparison, risk_tolerance, market_environment)

        return {
            'market_environment': market_environment,
            'risk_tolerance': risk_tolerance,
            'models_results': models_results,
            'comparison': comparison,
            'recommended_model': recommended_model,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    # ========== 私有方法 ==========

    def _calculate_covariance_matrix(self) -> np.ndarray:
        """计算协方差矩阵"""
        # 将相关性和波动率转换为协方差
        cov_matrix = np.zeros((len(self.assets), len(self.assets)))

        for i, asset_i in enumerate(self.assets):
            for j, asset_j in enumerate(self.assets):
                correlation = self.DEFAULT_CORRELATION[i][j]
                vol_i = self.DEFAULT_VOLATILITY[asset_i]
                vol_j = self.DEFAULT_VOLATILITY[asset_j]
                cov_matrix[i][j] = correlation * vol_i * vol_j

        return cov_matrix

    async def _identify_market_environment(self) -> str:
        """
        识别当前市场环境

        Returns:
            市场环境: 牛市/熊市/震荡市
        """
        # TODO: 集成MacroEconomicAI和其他AI进行判断
        # 目前返回默认值
        return MarketEnvironment.VOLATILE

    def _optimize_min_risk(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray
    ) -> np.ndarray:
        """最小化风险优化"""
        n_assets = len(expected_returns)

        # 目标函数：组合方差
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        # 约束：权重和为1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

        # 边界：权重在0-1之间（不允许卖空）
        bounds = tuple((0, 1) for _ in range(n_assets))

        # 初始权重：等权重
        initial_weights = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            portfolio_variance,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return result.x

    def _optimize_max_return(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray
    ) -> np.ndarray:
        """最大化收益优化"""
        n_assets = len(expected_returns)

        # 目标函数：负收益（最小化负收益 = 最大化收益）
        def negative_return(weights):
            return -np.dot(weights, expected_returns)

        # 约束：权重和为1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

        # 边界：权重在0-1之间
        bounds = tuple((0, 1) for _ in range(n_assets))

        # 初始权重：等权重
        initial_weights = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            negative_return,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return result.x

    def _optimize_max_sharpe(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_free_rate: float
    ) -> np.ndarray:
        """最大化夏普比率优化"""
        n_assets = len(expected_returns)

        # 目标函数：负夏普比率（最小化负夏普 = 最大化夏普）
        def negative_sharpe(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)
            return -(portfolio_return - risk_free_rate) / portfolio_std

        # 约束：权重和为1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

        # 边界：权重在0-1之间
        bounds = tuple((0, 1) for _ in range(n_assets))

        # 初始权重：等权重
        initial_weights = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            negative_sharpe,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return result.x

    def _optimize_risk_parity(
        self,
        cov_matrix: np.ndarray,
        risk_budget: Dict[str, float]
    ) -> np.ndarray:
        """风险平价优化"""
        n_assets = len(self.assets)

        # 目标函数：风险贡献与预算的偏差平方和
        def risk_parity_objective(weights):
            # 计算组合风险
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)

            # 计算每个资产的边际风险贡献
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_std

            # 计算每个资产的风险贡献
            risk_contributions = weights * marginal_contrib

            # 归一化风险贡献
            risk_contributions = risk_contributions / np.sum(risk_contributions)

            # 计算与风险预算的偏差
            target_contributions = np.array([risk_budget[asset.value] for asset in self.assets])
            return np.sum((risk_contributions - target_contributions) ** 2)

        # 约束：权重和为1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

        # 边界：权重在0-1之间
        bounds = tuple((0, 1) for _ in range(n_assets))

        # 初始权重：等权重
        initial_weights = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            risk_parity_objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return result.x

    def _apply_black_litterman_views(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        views: List[Dict[str, Any]],
        confidence: float
    ) -> np.ndarray:
        """应用Black-Litterman观点调整预期收益"""
        # TODO: 实现完整的Black-Litterman公式
        # 目前简化处理：根据置信度调整预期收益

        adjusted_returns = expected_returns.copy()

        for view in views:
            asset_idx = self.assets.index(
                AssetClass(view['asset'])
            )
            view_return = view.get('return', 0)

            # 根据置信度调整
            adjusted_returns[asset_idx] = (
                (1 - confidence) * expected_returns[asset_idx] +
                confidence * view_return
            )

        return adjusted_returns

    def _get_target_allocation_by_environment(
        self,
        market_environment: str
    ) -> Dict[str, float]:
        """根据市场环境获取目标配置"""
        if market_environment == MarketEnvironment.BULL:
            # 牛市：高配股票
            return {
                AssetClass.EQUITY.value: 0.50,  # 股票 50%
                AssetClass.BOND.value: 0.20,  # 债券 20%
                AssetClass.CASH.value: 0.05,  # 现金 5%
                AssetClass.COMMODITY.value: 0.15,  # 商品 15%
                AssetClass.REAL_ESTATE.value: 0.10,  # 房地产 10%
            }
        elif market_environment == MarketEnvironment.BEAR:
            # 熊市：高配债券和现金
            return {
                AssetClass.EQUITY.value: 0.15,  # 股票 15%
                AssetClass.BOND.value: 0.40,  # 债券 40%
                AssetClass.CASH.value: 0.25,  # 现金 25%
                AssetClass.COMMODITY.value: 0.10,  # 商品 10%
                AssetClass.REAL_ESTATE.value: 0.10,  # 房地产 10%
            }
        else:  # VOLATILE (震荡市)
            # 震荡市：均衡配置
            return {
                AssetClass.EQUITY.value: 0.30,  # 股票 30%
                AssetClass.BOND.value: 0.30,  # 债券 30%
                AssetClass.CASH.value: 0.15,  # 现金 15%
                AssetClass.COMMODITY.value: 0.10,  # 商品 10%
                AssetClass.REAL_ESTATE.value: 0.15,  # 房地产 15%
            }

    def _calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray
    ) -> Dict[str, float]:
        """计算组合指标"""
        # 预期收益
        portfolio_return = np.dot(weights, expected_returns)

        # 预期风险（标准差）
        portfolio_variance = np.dot(weights.T, np.dot(self.covariance_matrix, weights))
        portfolio_std = np.sqrt(portfolio_variance)

        # 夏普比率（假设无风险利率3%）
        risk_free_rate = 0.03
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std

        # 分散化比率（组合风险 / 加权平均风险）
        weighted_avg_risk = np.sum(weights * np.diag(self.covariance_matrix) ** 0.5)
        diversification_ratio = portfolio_std / weighted_avg_risk if weighted_avg_risk > 0 else 1.0

        return {
            'expected_return': round(portfolio_return, 4),
            'expected_risk': round(portfolio_std, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'diversification_ratio': round(diversification_ratio, 4)
        }

    def _format_allocation_result(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        portfolio_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """格式化配置结果"""
        allocation = {}

        for i, asset in enumerate(self.assets):
            asset_volatility = self.DEFAULT_VOLATILITY[asset]
            asset_return = expected_returns[i]

            allocation[asset.value] = {
                'ratio': round(weights[i], 4),
                'expected_return': round(asset_return, 4),
                'risk': round(asset_volatility, 4),
                'suggestion': self._get_asset_suggestion(asset, weights[i])
            }

        return {
            'allocation': allocation,
            'portfolio_metrics': portfolio_metrics
        }

    def _get_asset_suggestion(self, asset: AssetClass, weight: float) -> str:
        """获取资产配置建议"""
        if weight == 0:
            return "不建议配置"
        elif weight < 0.1:
            return f"低配{asset.value}"
        elif weight < 0.3:
            return f"标配{asset.value}"
        elif weight < 0.5:
            return f"超配{asset.value}"
        else:
            return f"重仓{asset.value}"

    def _generate_adjustment_suggestions(
        self,
        allocation_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成调整建议"""
        suggestions = []

        # TODO: 如果有当前配置，生成具体的调整建议
        # 目前返回空列表
        return suggestions

    def _generate_risk_warnings(
        self,
        allocation_result: Dict[str, Any]
    ) -> List[str]:
        """生成风险提示"""
        warnings = []

        portfolio_metrics = allocation_result['portfolio_metrics']

        # 1. 风险过高警告
        if portfolio_metrics['expected_risk'] > 0.15:
            warnings.append(f"组合预期风险较高({portfolio_metrics['expected_risk']:.2%})，建议降低风险资产配置")

        # 2. 收益过低警告
        if portfolio_metrics['expected_return'] < 0.05:
            warnings.append(f"组合预期收益较低({portfolio_metrics['expected_return']:.2%})，可能无法跑赢通胀")

        # 3. 夏普比率警告
        if portfolio_metrics['sharpe_ratio'] < 0.5:
            warnings.append(f"组合夏普比率较低({portfolio_metrics['sharpe_ratio']:.2f})，风险调整后收益不理想")

        # 4. 集中度警告
        allocation = allocation_result['allocation']
        max_weight = max([item['ratio'] for item in allocation.values()])
        if max_weight > 0.6:
            warnings.append(f"单一资产配置比例过高({max_weight:.2%})，建议适当分散")

        return warnings

    def _compare_models(
        self,
        models_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """对比不同模型的结果"""
        comparison = {
            'expected_return': {},
            'expected_risk': {},
            'sharpe_ratio': {}
        }

        for model_name, result in models_results.items():
            metrics = result['portfolio_metrics']
            comparison['expected_return'][model_name] = metrics['expected_return']
            comparison['expected_risk'][model_name] = metrics['expected_risk']
            comparison['sharpe_ratio'][model_name] = metrics['sharpe_ratio']

        return comparison

    def _recommend_model(
        self,
        comparison: Dict[str, Any],
        risk_tolerance: float,
        market_environment: str
    ) -> Dict[str, Any]:
        """推荐最优模型"""
        # 根据风险容忍度和市场环境推荐模型

        if risk_tolerance > 0.7:
            # 激进投资者：推荐均值方差模型（最大化收益）
            recommended = 'mean_variance'
            reason = "激进投资者，推荐使用均值方差模型以最大化收益"
        elif risk_tolerance < 0.3:
            # 保守投资者：推荐风险平价模型（风险分散）
            recommended = 'risk_parity'
            reason = "保守投资者，推荐使用风险平价模型以实现风险分散"
        else:
            # 中性投资者：推荐Black-Litterman模型（结合市场均衡）
            recommended = 'black_litterman'
            reason = "中性投资者，推荐使用Black-Litterman模型以平衡收益和风险"

        return {
            'model': recommended,
            'reason': reason,
            'expected_return': comparison['expected_return'][recommended],
            'expected_risk': comparison['expected_risk'][recommended],
            'sharpe_ratio': comparison['sharpe_ratio'][recommended]
        }

    def format_allocation_report(self, allocation_result: Dict[str, Any]) -> str:
        """格式化资产配置报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("资产配置报告")
        lines.append("=" * 80)
        lines.append(f"配置日期: {allocation_result.get('allocation_date', 'N/A')}")
        lines.append(f"使用模型: {allocation_result.get('model_used', 'N/A')}")
        lines.append(f"市场环境: {allocation_result.get('macro_environment', 'N/A')}")
        lines.append("")

        # 资产配置
        lines.append("-" * 80)
        lines.append("资产配置:")
        allocation = allocation_result['allocation']
        for asset_name, asset_info in allocation.items():
            lines.append(f"  {asset_name}:")
            lines.append(f"    - 配置比例: {asset_info['ratio']:.2%}")
            lines.append(f"    - 预期收益: {asset_info['expected_return']:.2%}")
            lines.append(f"    - 预期风险: {asset_info['risk']:.2%}")
            lines.append(f"    - 配置建议: {asset_info['suggestion']}")
        lines.append("")

        # 组合指标
        lines.append("-" * 80)
        lines.append("组合指标:")
        metrics = allocation_result['portfolio_metrics']
        lines.append(f"  预期收益率: {metrics['expected_return']:.2%}")
        lines.append(f"  预期风险: {metrics['expected_risk']:.2%}")
        lines.append(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
        lines.append(f"  分散化比率: {metrics['diversification_ratio']:.2f}")
        lines.append("")

        # 风险提示
        if allocation_result.get('risk_warnings'):
            lines.append("-" * 80)
            lines.append("风险提示:")
            for warning in allocation_result['risk_warnings']:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)
