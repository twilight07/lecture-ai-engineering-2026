"""第3回 宿題（実装）: save_learning_log と承認の流れのテスト（LLMもAPIキーも使わない）。"""

import pytest
from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, run_with_approval


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    return tmp_path / "learning_log"


def test_save_learning_log_writes_markdown(log_dir):
    message = tools.save_learning_log("LoRAとQLoRA", "- QLoRA は量子化したモデルに LoRA を足す")
    files = list(log_dir.glob("*.md"))
    assert len(files) == 1 and "保存しました" in message
    text = files[0].read_text(encoding="utf-8")
    assert text.startswith("# LoRAとQLoRA") and "量子化" in text


def test_save_learning_log_does_not_repeat_heading(log_dir):
    tools.save_learning_log("PEFT", "# PEFTについて\n\n本文")
    text = next(log_dir.glob("*.md")).read_text(encoding="utf-8")
    assert text.count("\n# ") + text.startswith("# ") == 1 and text.startswith("# PEFTについて")


def test_save_learning_log_stays_inside_log_dir(log_dir):
    tools.save_learning_log("../../etc/passwd", "本文")
    tools.save_learning_log("../../etc/passwd", "本文")  # 同じ題名でも上書きしない
    files = list(log_dir.glob("*.md"))
    assert len(files) == 2
    assert all(f.parent == log_dir for f in files)


def test_save_learning_log_rejects_empty(log_dir):
    assert "保存はしていません" in tools.save_learning_log(" ", "本文")
    assert not log_dir.exists()


def test_save_learning_log_waits_for_approval(log_dir):
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        result = agent.run_sync("今日の学びを記録して")
    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert not log_dir.exists()  # 承認されるまで保存されない


@pytest.mark.parametrize("answer, saved", [("y", True), ("n", False), ("", False)])
def test_run_with_approval(log_dir, answer, saved, capsys):
    asked = []

    def ask(prompt):
        asked.append(prompt)
        return answer

    model = TestModel(call_tools=["save_learning_log"])
    result = run_with_approval(agent, "今日の学びを記録して", model, ask=ask)

    assert len(asked) == 1
    assert result.usage.requests >= 2  # 承認の前と後の両方を数える
    assert "[approval] save_learning_log" in capsys.readouterr().out
    assert isinstance(result.output, str)
    assert (len(list(log_dir.glob("*.md"))) == 1 if saved else not log_dir.exists())
    returns = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolReturnPart)]
    expected = "保存しました" if saved else "断りました"
    assert any(expected in str(p.content) for p in returns if p.tool_name == "save_learning_log")
