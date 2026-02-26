"""LLM 配置 — 支持 OpenAI、Kimi 等兼容 API"""
import os
from pathlib import Path
from typing import Optional, Tuple

def _load_env_file_fallback(env_path: Path) -> None:
    """在 python-dotenv 不可用时，最小化解析 .env 文件。"""
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key:
                os.environ.setdefault(key, value)
    except Exception:
        # 配置读取失败时保持静默，不影响主流程
        pass


def _load_env_candidates(work_dir: Optional[Path] = None) -> None:
    """加载多个候选 .env 位置，优先使用 work_dir。"""
    candidates = []
    if work_dir:
        candidates.append(Path(work_dir) / ".env")
    candidates.extend([Path.cwd() / ".env", Path.home() / ".env"])

    # 去重并保持顺序
    seen = set()
    deduped = []
    for p in candidates:
        key = str(p.resolve()) if p.exists() else str(p)
        if key not in seen:
            deduped.append(p)
            seen.add(key)

    for env_path in deduped:
        if not env_path.exists():
            continue
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=False)
        except ImportError:
            _load_env_file_fallback(env_path)
        except Exception:
            # 任一 .env 读取失败不应中断主流程
            continue


def get_llm_config(work_dir: Optional[Path] = None) -> Tuple[Optional[str], Optional[str], str]:
    """
    获取 LLM 配置。
    返回 (api_key, base_url, model)
    """
    _load_env_candidates(work_dir)
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ARDUINO_CLIENT_API_KEY")
    base_url = os.environ.get("OPENAI_API_BASE") or os.environ.get("ARDUINO_CLIENT_API_BASE")
    model = os.environ.get("OPENAI_MODEL") or os.environ.get("ARDUINO_CLIENT_MODEL") or "gpt-4o-mini"

    # 尝试从 config.yaml 读取 base_url、model（api_key 建议用环境变量）
    if work_dir:
        config_path = Path(work_dir) / "config" / "config.yaml"
        if config_path.exists():
            try:
                import yaml
                with open(config_path, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                if cfg and "llm" in cfg:
                    llm = cfg["llm"]
                    api_key = api_key or llm.get("api_key")
                    base_url = base_url or llm.get("base_url")
                    model = llm.get("model") or model
            except Exception:
                pass

    return api_key, base_url, model


def is_llm_configured(work_dir: Optional[Path] = None) -> bool:
    """检查 LLM 是否已配置"""
    api_key, _, _ = get_llm_config(work_dir)
    return bool(api_key)
