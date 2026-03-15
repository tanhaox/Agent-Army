"""
Experience Accumulation AI - Record investment paths and build experience database
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from enum import Enum
import json
from pathlib import Path

from src.core.base_agent import BaseAgent, AgentCapability
from src.core.logger import LoggerMixin


class CaseStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class CaseType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


class ExperienceAccumulationAI(BaseAgent, LoggerMixin):
    """
    Experience Accumulation AI

    Core Functions:
    1. Record investment path (analysis -> prediction -> verification)
    2. Build experience database (success, failure, pending)
    3. Provide case query
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.experience_db_path = Path(config.get("experience_db_path", "data/experience_db.json"))
        self.experience_db_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(
            name="Experience Accumulation AI",
            role="Record investment paths, build experience database",
            capabilities=[
                AgentCapability(
                    name="record_investment_path",
                    description="Record investment path",
                    input_type="investment_path",
                    output_type="record_id"
                ),
                AgentCapability(
                    name="query_experience",
                    description="Query experience cases",
                    input_type="query_criteria",
                    output_type="experience_list"
                ),
                AgentCapability(
                    name="verify_prediction",
                    description="Verify prediction accuracy",
                    input_type="record_id_actual_result",
                    output_type="verification_report"
                ),
            ]
        )

        self.experience_db = self._load_experience_db()

        self.logger.info(f"Experience Accumulation AI initialized")
        self.logger.info(f"Experience DB: {self.experience_db_path}")
        self.logger.info(f"Total records: {len(self.experience_db)}")

    async def record_investment_path(
        self,
        stock_code: str,
        dimensions: Dict[str, Any],
        prediction: Dict[str, Any],
        analysis_date: Optional[date] = None
    ) -> str:
        """
        Record investment path

        Args:
            stock_code: Stock code
            dimensions: 6-dimension analysis data
            prediction: Prediction (6 core indicators)
            analysis_date: Analysis date

        Returns:
            record_id
        """
        self.logger.info(f"Recording investment path: {stock_code}")

        analysis_date = analysis_date or date.today()
        record_id = f"{stock_code}_{analysis_date.strftime('%Y%m%d')}"

        investment_path = {
            "record_id": record_id,
            "stock_code": stock_code,
            "analysis_date": analysis_date.strftime('%Y-%m-%d'),
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

            "dimensions": {
                "fundamental": dimensions.get("fundamental", {}),
                "technical": dimensions.get("technical", {}),
                "capital": dimensions.get("capital", {}),
                "policy": dimensions.get("policy", {}),
                "historical": dimensions.get("historical", {}),
                "industry": dimensions.get("industry", {}),
            },

            "prediction": {
                "stop_loss": prediction.get("stop_loss", 0.0),
                "buy_price": prediction.get("buy_price", 0.0),
                "cost_price": prediction.get("cost_price", 0.0),
                "resistance": prediction.get("resistance", []),
                "time_window": prediction.get("time_window", ""),
                "target_price": prediction.get("target_price", 0.0),
                "confidence": prediction.get("confidence", 0.0),
            },

            "actual_result": {
                "actual_stop_loss": None,
                "actual_buy_price": None,
                "actual_target_price": None,
                "actual_time_window": "",
                "accuracy": None,
                "deviation": None,
                "verified_date": None,
            },

            "status": CaseStatus.PENDING.value,
            "case_type": CaseType.PENDING.value,
        }

        self.experience_db[record_id] = investment_path
        self._save_experience_db()

        self.logger.info(f"Record created: {record_id}")
        self.logger.info(f"  - Stop Loss: {prediction.get('stop_loss', 0):.2f}")
        self.logger.info(f"  - Buy Price: {prediction.get('buy_price', 0):.2f}")
        self.logger.info(f"  - Target Price: {prediction.get('target_price', 0):.2f}")
        self.logger.info(f"  - Time Window: {prediction.get('time_window', '')}")
        self.logger.info(f"  - Confidence: {prediction.get('confidence', 0):.1%}")

        return record_id

    async def verify_prediction(
        self,
        record_id: str,
        actual_stop_loss: Optional[float] = None,
        actual_buy_price: Optional[float] = None,
        actual_target_price: Optional[float] = None,
        actual_time_window: Optional[str] = None,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Verify prediction accuracy

        Args:
            record_id: Record ID
            actual_stop_loss: Actual stop loss price
            actual_buy_price: Actual buy price
            actual_target_price: Actual target price
            actual_time_window: Actual time window
            current_price: Current price

        Returns:
            Verification report
        """
        self.logger.info(f"Verifying prediction: {record_id}")

        if record_id not in self.experience_db:
            raise ValueError(f"Record not found: {record_id}")

        record = self.experience_db[record_id]
        prediction = record["prediction"]

        accuracy = self._calculate_accuracy(prediction, {
            "actual_stop_loss": actual_stop_loss,
            "actual_buy_price": actual_buy_price,
            "actual_target_price": actual_target_price,
            "actual_time_window": actual_time_window,
            "current_price": current_price
        })

        deviation = self._calculate_deviation(prediction, {
            "actual_stop_loss": actual_stop_loss,
            "actual_buy_price": actual_buy_price,
            "actual_target_price": actual_target_price,
            "current_price": current_price
        })

        case_type = self._determine_case_type(accuracy, deviation)

        record["actual_result"] = {
            "actual_stop_loss": actual_stop_loss,
            "actual_buy_price": actual_buy_price,
            "actual_target_price": actual_target_price,
            "actual_time_window": actual_time_window,
            "accuracy": accuracy,
            "deviation": deviation,
            "verified_date": date.today().strftime('%Y-%m-%d'),
        }
        record["status"] = CaseStatus.VERIFIED.value
        record["case_type"] = case_type.value

        # 生成验证摘要并保存到记录中
        verification_summary = self._generate_verification_summary(record)
        record["verification_summary"] = verification_summary

        self.experience_db[record_id] = record
        self._save_experience_db()

        report = {
            "record_id": record_id,
            "stock_code": record["stock_code"],
            "case_type": case_type.value,
            "accuracy": accuracy,
            "deviation": deviation,
            "verification_summary": verification_summary,
        }

        self.logger.info(f"Prediction verified: {record_id}")
        self.logger.info(f"  - Case Type: {case_type.value}")
        self.logger.info(f"  - Accuracy: {accuracy:.1%}")
        self.logger.info(f"  - Deviation: {deviation:.1%}")

        return report

    async def query_experience(
        self,
        stock_code: Optional[str] = None,
        case_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query experience cases

        Args:
            stock_code: Stock code filter
            case_type: Case type filter (success/failure/pending)
            status: Status filter
            limit: Return limit

        Returns:
            Experience case list
        """
        self.logger.info(f"Querying experience: stock_code={stock_code}, case_type={case_type}")

        results = []

        for record_id, record in self.experience_db.items():
            if stock_code and record["stock_code"] != stock_code:
                continue
            if case_type and record["case_type"] != case_type:
                continue
            if status and record["status"] != status:
                continue

            results.append(record)

            if len(results) >= limit:
                break

        self.logger.info(f"Found {len(results)} cases")

        return results

    def _calculate_accuracy(
        self,
        prediction: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> float:
        """Calculate prediction accuracy"""
        accuracy = 0.5

        if actual.get("actual_target_price"):
            target_price = prediction["target_price"]
            actual_target = actual["actual_target_price"]

            if target_price > 0:
                if actual_target >= target_price * 0.8:
                    accuracy = 1.0
                elif actual_target >= target_price * 0.5:
                    accuracy = 0.7
                else:
                    accuracy = 0.3

        if actual.get("current_price"):
            current_price = actual["current_price"]
            buy_price = prediction["buy_price"]

            if buy_price > 0 and current_price > 0:
                price_ratio = current_price / buy_price
                if 0.9 <= price_ratio <= 1.2:
                    accuracy = max(accuracy, 0.8)
                elif 0.8 <= price_ratio <= 1.5:
                    accuracy = max(accuracy, 0.6)
                else:
                    accuracy = min(accuracy, 0.3)

        return accuracy

    def _calculate_deviation(
        self,
        prediction: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> float:
        """Calculate deviation"""
        deviation = 0.5

        if actual.get("actual_target_price"):
            target_price = prediction["target_price"]
            actual_target = actual["actual_target_price"]

            if target_price > 0:
                price_deviation = abs(actual_target - target_price) / target_price
                deviation = min(price_deviation, 1.0)

        return deviation

    def _determine_case_type(
        self,
        accuracy: float,
        deviation: float
    ) -> CaseType:
        """Determine case type"""
        if accuracy >= 0.7 and deviation < 0.3:
            return CaseType.SUCCESS
        elif accuracy < 0.5 or deviation > 0.5:
            return CaseType.FAILURE
        else:
            return CaseType.PENDING

    def _generate_verification_summary(self, record: Dict[str, Any]) -> str:
        """Generate verification summary"""
        prediction = record["prediction"]
        actual = record["actual_result"]
        case_type = record["case_type"]

        summary_parts = []

        summary_parts.append(f"Predict: Target {prediction['target_price']:.2f}")
        summary_parts.append(f"Buy {prediction['buy_price']:.2f}")
        summary_parts.append(f"Stop {prediction['stop_loss']:.2f}")

        if actual.get("actual_target_price"):
            summary_parts.append(f"Actual {actual['actual_target_price']:.2f}")

        if case_type == CaseType.SUCCESS.value:
            summary_parts.append("[OK] Accurate")
        elif case_type == CaseType.FAILURE.value:
            summary_parts.append("[FAIL] Deviated")
        else:
            summary_parts.append("[WARN] Partial")

        return " | ".join(summary_parts)

    def _load_experience_db(self) -> Dict[str, Any]:
        """Load experience database"""
        if self.experience_db_path.exists():
            try:
                with open(self.experience_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load experience DB: {e}")
                return {}
        else:
            return {}

    def _save_experience_db(self):
        """Save experience database"""
        try:
            with open(self.experience_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.experience_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save experience DB: {e}")

    async def execute(self, task: str, **kwargs) -> Any:
        """
        Execute task

        Args:
            task: Task name
            **kwargs: Task arguments

        Returns:
            Task result
        """
        if task == "record":
            return await self.record_investment_path(
                stock_code=kwargs.get("stock_code"),
                dimensions=kwargs.get("dimensions", {}),
                prediction=kwargs.get("prediction", {})
            )
        elif task == "verify":
            return await self.verify_prediction(
                record_id=kwargs.get("record_id"),
                actual_stop_loss=kwargs.get("actual_stop_loss"),
                actual_buy_price=kwargs.get("actual_buy_price"),
                actual_target_price=kwargs.get("actual_target_price"),
                current_price=kwargs.get("current_price")
            )
        elif task == "query":
            return await self.query_experience(
                stock_code=kwargs.get("stock_code"),
                case_type=kwargs.get("case_type"),
                limit=kwargs.get("limit", 10)
            )
        elif task == "statistics":
            return await self.get_statistics()
        else:
            raise ValueError(f"Unknown task: {task}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get experience database statistics"""
        total_cases = len(self.experience_db)

        success_cases = sum(1 for r in self.experience_db.values() if r["case_type"] == CaseType.SUCCESS.value)
        failure_cases = sum(1 for r in self.experience_db.values() if r["case_type"] == CaseType.FAILURE.value)
        pending_cases = sum(1 for r in self.experience_db.values() if r["case_type"] == CaseType.PENDING.value)

        return {
            "total_cases": total_cases,
            "success_cases": success_cases,
            "failure_cases": failure_cases,
            "pending_cases": pending_cases,
            "success_rate": success_cases / total_cases if total_cases > 0 else 0,
        }
