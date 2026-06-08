#!/usr/bin/env python3
"""
export_predictions_json.py - 从DuckDB导出预测数据到JSON（v2.0）
适配实际表结构，使用 read_only 连接避免锁冲突。
"""
import json
import duckdb
import time
from pathlib import Path
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/data/predictions.db"
OUTPUT_DIR = Path("/root/.openclaw/workspace/data/prediction_accuracy/json")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def export_predictions():
    """导出预测数据到JSON"""
    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
    except Exception as e:
        print(f"连接失败: {e}")
        return False

    try:
        # 1. 导出 predictions.json
        rows = conn.execute("""
            SELECT prediction_id, stock_code, analysis_date, total_score,
                   recommendation, position_advice, confidence_level,
                   reasoning, source, is_strong_signal, is_backtest,
                   verified, is_correct, actual_result, actual_return_5d,
                   verified_time, created_at
            FROM predictions
            ORDER BY analysis_date DESC
        """).fetchall()

        predictions = []
        for r in rows:
            predictions.append({
                'id': r[0],
                'stock_code': r[1],
                'analysis_date': str(r[2]) if r[2] else None,
                'total_score': round(r[3], 2) if r[3] else None,
                'recommendation': r[4],
                'position_advice': r[5],
                'confidence_level': r[6],
                'reasoning': r[7][:200] + '...' if r[7] and len(str(r[7])) > 200 else r[7],
                'source': r[8],
                'is_strong_signal': r[9],
                'is_backtest': r[10],
                'verified': r[11],
                'is_correct': r[12],
                'actual_result': r[13],
                'actual_return_5d': round(r[14], 2) if r[14] else None,
                'verified_time': str(r[15]) if r[15] else None,
                'created_at': str(r[16]) if r[16] else None,
            })

        with open(OUTPUT_DIR / "predictions.json", 'w', encoding='utf-8') as f:
            json.dump({'predictions': predictions, 'export_time': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        print(f"predictions.json: {len(predictions)} 条")

        # 2. 导出 results.json（按股票汇总）
        rows = conn.execute("""
            SELECT stock_code,
                   COUNT(*) as total,
                   SUM(CASE WHEN verified THEN 1 ELSE 0 END) as verified_count,
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                   ROUND(AVG(CASE WHEN actual_return_5d IS NOT NULL THEN actual_return_5d END), 2) as avg_return
            FROM predictions
            GROUP BY stock_code
            ORDER BY total DESC
        """).fetchall()

        results = []
        for r in rows:
            acc = round(r[3] / r[2] * 100, 1) if r[2] and r[2] > 0 else None
            results.append({
                'stock_code': r[0], 'total': r[1], 'verified': r[2],
                'correct': r[3], 'accuracy': acc, 'avg_return': r[4]
            })

        with open(OUTPUT_DIR / "results.json", 'w', encoding='utf-8') as f:
            json.dump({'results': results, 'export_time': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        print(f"results.json: {len(results)} 只股票")

        # 3. 导出 confidence.json（按置信度汇总）
        rows = conn.execute("""
            SELECT confidence_level,
                   COUNT(*) as total,
                   SUM(CASE WHEN verified THEN 1 ELSE 0 END) as verified_count,
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
            FROM predictions
            WHERE confidence_level IS NOT NULL
            GROUP BY confidence_level
        """).fetchall()

        confidence = {}
        for r in rows:
            level = r[0] or 'unknown'
            acc = round(r[3] / r[2] * 100, 1) if r[2] and r[2] > 0 else None
            confidence[level] = {
                'total': r[1], 'verified': r[2], 'correct': r[3],
                'accuracy': acc
            }

        # 整体准确率
        overall = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN verified THEN 1 ELSE 0 END) as verified,
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
            FROM predictions
        """).fetchone()
        overall_acc = round(overall[2] / overall[1] * 100, 1) if overall[1] and overall[1] > 0 else 0
        confidence['overall'] = {
            'total': overall[0], 'verified': overall[1],
            'correct': overall[2], 'accuracy': overall_acc
        }

        with open(OUTPUT_DIR / "confidence.json", 'w', encoding='utf-8') as f:
            json.dump({'confidence': confidence, 'export_time': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        print(f"confidence.json: 整体准确率 {overall_acc}% ({overall[2]}/{overall[1]})")

        # 4. 导出 summary.json
        summary = {
            'total_predictions': overall[0],
            'verified': overall[1],
            'correct': overall[2],
            'accuracy': overall_acc,
            'last_analysis_date': str(conn.execute("SELECT MAX(analysis_date) FROM predictions").fetchone()[0]),
            'export_time': datetime.now().isoformat()
        }
        with open(OUTPUT_DIR / "summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"summary.json: {summary['total_predictions']} 条预测, 准确率 {overall_acc}%")

        conn.close()
        return True

    except Exception as e:
        print(f"导出失败: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return False


if __name__ == "__main__":
    export_predictions()
