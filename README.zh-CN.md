<div align="center">
  <h1>CI Queue Doctor</h1>
  <p><strong>用证据解释 GitHub Actions 在等待什么，而不是猜原因。</strong></p>
  <p>
    <a href="https://github.com/cuijialin8888-code/ci-queue-doctor/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/cuijialin8888-code/ci-queue-doctor/actions/workflows/ci.yml/badge.svg"></a>
    <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
    <img alt="运行时依赖：0" src="https://img.shields.io/badge/runtime%20dependencies-0-10b981">
    <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-0f172"></a>
  </p>
</div>

GitHub Actions 可能长时间处于 `queued`，但界面不一定直接告诉你是在等待
Runner、并发槽位、环境审批，还是矩阵依赖。CI Queue Doctor 读取公开的运行和
Job 数据，把当前能观察到的状态整理成小而可审计的报告。

它有明确边界：

- **只读 GET：** 不触发、重跑、取消、批准或修改工作流。
- **证据优先：** 每条发现都列出触发它的字段。
- **诚实表达不确定性：** 不冒充知道 GitHub 内部调度器的真实原因。
- **零运行时依赖：** CLI 只使用 Python 标准库。

## 快速开始

```console
python -m ci_queue_doctor --repo OWNER/REPOSITORY
```

检查指定运行并输出 JSON：

```console
python -m ci_queue_doctor --repo OWNER/REPOSITORY --run 123456789 --threshold 5 --format json
```

公开仓库通常无需令牌。私有仓库或需要更高 API 配额时，建议通过环境变量提供
短期令牌，而不是把令牌写入命令历史：

```powershell
$env:GH_TOKEN = "github_pat_..."
python -m ci_queue_doctor --repo OWNER/REPOSITORY
```

令牌只作为 HTTPS `Authorization` 请求头发送，不会写入报告。不要把令牌粘贴到
Issue、日志或报告中。

## 发现编号

`CQD001`–`CQD099` 是稳定编号，便于自动化处理。默认报告包括：运行超过本地阈值、
尚无 Job、Job 排队、运行中仍有排队 Job、Job 处于 `waiting`、非成功结束，以及未知
状态。阈值只是本地观察窗口，不是 GitHub 内部调度故障的证明。详见
[安全与证据边界](docs/safety.md)。

## 输出与开发

`--format` 支持 `text`、`json`、`markdown`、`sarif`。使用 `--fail-on warning` 或
`--fail-on error` 可让监控作业在发现问题时返回退出码 1。

```console
python -m venv .venv
.venv\Scripts\python -m pip install --index-url https://pypi.org/simple -e ".[dev]"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check src tests
```

项目支持 Python 3.10–3.13，运行时无第三方依赖。完整边界和 API 链接见英文
[README](README.md)。

## 许可证

MIT，见 [LICENSE](LICENSE)。
