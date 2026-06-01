import logging
import json
import os
from datetime import datetime
from typing import Any, Dict

class IndustryLogger:
    """
    Structured logger that simulates industry practices.
    Logs structured JSON to a .log file and beautiful human-readable text to a .readable.log file.
    """
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 1. Logger for JSON lines (.log file)
        self.json_logger = logging.getLogger(f"{name}-JSON")
        self.json_logger.setLevel(logging.INFO)
        self.json_logger.handlers.clear()
        self.json_logger.propagate = False
        
        json_log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        json_handler = logging.FileHandler(json_log_file, encoding="utf-8")
        self.json_logger.addHandler(json_handler)

        # 2. Logger for human-readable text logs (.readable.log file and console)
        self.readable_logger = logging.getLogger(f"{name}-Readable")
        self.readable_logger.setLevel(logging.INFO)
        self.readable_logger.handlers.clear()
        self.readable_logger.propagate = False
        
        readable_log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.readable.log")
        readable_handler = logging.FileHandler(readable_log_file, encoding="utf-8")
        console_handler = logging.StreamHandler()
        
        self.readable_logger.addHandler(readable_handler)
        self.readable_logger.addHandler(console_handler)

    def _format_readable(self, event_type: str, timestamp: str, data: Dict[str, Any]) -> str:
        border = "=" * 80
        section_sep = "-" * 80
        
        lines = []
        lines.append(border)
        lines.append(f"[{timestamp}] EVENT: {event_type}")
        lines.append(section_sep)
        
        if event_type == "AGENT_START":
            lines.append(f"  User Input : {data.get('input', '')}")
            lines.append(f"  Model      : {data.get('model', '')}")
            
        elif event_type == "LLM_RESPONSE":
            lines.append(f"  Step       : {data.get('step', '')}")
            lines.append("  Raw Response:")
            lines.append(section_sep)
            raw_text = data.get('raw_text', '')
            indented_text = "\n".join(f"    {line}" for line in raw_text.splitlines())
            lines.append(indented_text)
            
        elif event_type == "AGENT_END":
            lines.append(f"  Total Steps: {data.get('steps', '')}")
            lines.append(f"  Status     : {data.get('status', '')}")
            metrics = data.get('metrics', {})
            if metrics:
                lines.append(section_sep)
                lines.append("  Accumulated Request Metrics:")
                lines.append(f"    Total Prompt Tokens     : {metrics.get('total_prompt_tokens', 0)}")
                lines.append(f"    Total Completion Tokens : {metrics.get('total_completion_tokens', 0)}")
                lines.append(f"    Total Tokens            : {metrics.get('total_tokens', 0)}")
                lines.append(f"    Total Latency           : {metrics.get('total_latency_ms', 0)} ms ({metrics.get('total_latency_ms', 0)/1000.0:.2f} s)")
                lines.append(f"    Total Cost              : ${metrics.get('total_cost', 0.0):.6f}")
            
        elif event_type == "LLM_METRIC":
            lines.append(f"  Provider          : {data.get('provider', '')}")
            lines.append(f"  Model             : {data.get('model', '')}")
            lines.append(f"  Prompt Tokens     : {data.get('prompt_tokens', 0)}")
            lines.append(f"  Completion Tokens : {data.get('completion_tokens', 0)}")
            lines.append(f"  Total Tokens      : {data.get('total_tokens', 0)}")
            lines.append(f"  Latency           : {data.get('latency_ms', 0)} ms")
            cost = data.get('cost_estimate', 0.0)
            lines.append(f"  Cost Estimate     : ${cost:.6f}")
            
        else:
            lines.append(json.dumps(data, indent=2, ensure_ascii=False))
            
        lines.append(border)
        lines.append("\n") # Additional space
        return "\n".join(lines)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Logs an event with a timestamp and type."""
        timestamp = datetime.utcnow().isoformat()
        payload = {
            "timestamp": timestamp,
            "event": event_type,
            "data": data
        }
        # Log JSON line (with encoding preserved and unescaped Unicode)
        self.json_logger.info(json.dumps(payload, ensure_ascii=False))
        
        # Log readable format to console and readable file
        readable_msg = self._format_readable(event_type, timestamp, data)
        self.readable_logger.info(readable_msg)

    def info(self, msg: str):
        self.readable_logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.readable_logger.error(msg, exc_info=exc_info)

# Global logger instance
logger = IndustryLogger()
