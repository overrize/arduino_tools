# 技术架构设计文档

## 1. 技术栈选型

| 组件 | 选型 | 版本要求 | 理由 |
|------|------|----------|------|
| **编程语言** | Python | 3.9+ | 已有项目基础，生态丰富，适合 CLI 工具开发 |
| **代码生成** | LLM API (OpenAI/Kimi) | OpenAI SDK 1.0+ | 支持自然语言理解，灵活性强 |
| **Arduino 工具链** | arduino-cli | 最新稳定版 | 官方命令行工具，支持编译、上传、板卡检测 |
| **串口通信** | pyserial | 3.5+ | Python 标准串口库，稳定可靠 |
| **配置管理** | python-dotenv | 1.0+ | 环境变量管理，支持 .env 文件 |
| **数据验证** | pydantic | 2.0+ | 类型安全，数据模型验证 |
| **终端 UI** | rich | 13.0+ (可选) | 美化交互式界面，提升用户体验 |
| **仿真平台** | Wokwi CLI | 最新版 | 支持 Arduino 仿真，可通过串口输出验证 |
| **进程管理** | psutil | 5.9+ | 进程检测和管理，用于串口占用检测 |
| **项目构建** | setuptools | 61.0+ | Python 包管理和分发 |

### 技术决策说明

1. **LLM API vs 模板驱动**
   - **选择**: LLM API
   - **理由**: 灵活性高，能处理复杂和多样化的需求，无需维护大量模板

2. **独立 Client vs MCP Server**
   - **选择**: 独立 Client（已有实现）
   - **理由**: 不依赖外部服务，使用简单，可编程 API 友好

3. **Wokwi vs Tinkercad**
   - **选择**: Wokwi
   - **理由**: 支持 CLI，可通过串口输出验证，更适合自动化测试

---

## 2. 数据模型定义

### 2.1 核心数据模型

```python
# models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from pathlib import Path

class BoardType(str, Enum):
    """支持的开发板类型"""
    UNO = "arduino:avr:uno"
    NANO = "arduino:avr:nano"
    PICO = "rp2040:rp2040:rpipico"
    ESP32 = "esp32:esp32:esp32"
    CUSTOM = "custom"  # 自定义板子

class BoardInfo(BaseModel):
    """板卡信息"""
    fqbn: str = Field(..., description="完全限定板名 (FQBN)")
    port: Optional[str] = Field(None, description="串口路径 (COM3, /dev/ttyUSB0)")
    name: Optional[str] = Field(None, description="板卡名称")
    type: BoardType = Field(..., description="板卡类型")
    is_connected: bool = Field(False, description="是否已连接")

class ProjectConfig(BaseModel):
    """项目配置"""
    name: str = Field(..., description="项目名称")
    description: str = Field("", description="项目描述")
    board_type: BoardType = Field(..., description="目标板卡类型")
    fqbn: str = Field(..., description="FQBN")
    port: Optional[str] = Field(None, description="上传端口")
    libraries: List[str] = Field(default_factory=list, description="依赖库列表")
    pins: Dict[str, int] = Field(default_factory=dict, description="引脚映射")
    created_at: str = Field(..., description="创建时间")

class CompileResult(BaseModel):
    """编译结果"""
    success: bool = Field(..., description="是否成功")
    output_path: Optional[Path] = Field(None, description="编译输出路径")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    compile_time: float = Field(0.0, description="编译耗时（秒）")

class UploadResult(BaseModel):
    """上传结果"""
    success: bool = Field(..., description="是否成功")
    port: Optional[str] = Field(None, description="上传端口")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    upload_time: float = Field(0.0, description="上传耗时（秒）")

class MonitorResult(BaseModel):
    """监控结果"""
    output: List[str] = Field(default_factory=list, description="串口输出")
    duration: float = Field(0.0, description="监控时长（秒）")
    matched_patterns: List[str] = Field(default_factory=list, description="匹配的期望模式")

class RequirementAnalysis(BaseModel):
    """需求分析结果"""
    board_type: BoardType = Field(..., description="识别的板卡类型")
    components: List[str] = Field(default_factory=list, description="识别的组件列表")
    libraries: List[str] = Field(default_factory=list, description="需要的库")
    pins: Dict[str, int] = Field(default_factory=dict, description="引脚需求")
    functions: List[str] = Field(default_factory=list, description="功能列表")
    confidence: float = Field(0.0, description="识别置信度 (0-1)")
    needs_clarification: bool = Field(False, description="是否需要澄清")
    clarification_questions: List[str] = Field(default_factory=list, description="澄清问题列表")

class SimulationConfig(BaseModel):
    """仿真配置"""
    project_path: Path = Field(..., description="项目路径")
    wokwi_config: Dict = Field(default_factory=dict, description="Wokwi 配置")
    diagram_json: Dict = Field(default_factory=dict, description="diagram.json 内容")
    wokwi_toml: Dict = Field(default_factory=dict, description="wokwi.toml 内容")
```

### 2.2 扩展数据模型（Story 5-7）

```python
class CustomBoardConfig(BaseModel):
    """自定义板子配置"""
    chip_type: str = Field(..., description="芯片类型")
    pin_mapping: Dict[str, int] = Field(..., description="引脚映射")
    board_name: str = Field(..., description="板子名称")
    fqbn: str = Field(..., description="自定义 FQBN")

class ModuleInfo(BaseModel):
    """模块信息"""
    name: str = Field(..., description="模块名称")
    type: str = Field(..., description="模块类型 (sensor/actuator/display)")
    library: Optional[str] = Field(None, description="推荐库")
    pins: List[int] = Field(default_factory=list, description="常用引脚")
    example_code: Optional[str] = Field(None, description="示例代码")

class CodeQualityMetrics(BaseModel):
    """代码质量指标"""
    has_comments: bool = Field(False, description="是否有注释")
    modularity_score: float = Field(0.0, description="模块化评分 (0-1)")
    follows_best_practices: bool = Field(False, description="是否遵循最佳实践")
    documentation_completeness: float = Field(0.0, description="文档完整度 (0-1)")
```

---

## 3. API 设计

### 3.1 ArduinoClient 核心 API（已有，需扩展）

```python
class ArduinoClient:
    """Arduino Client 核心 API"""
    
    # ========== 现有 API（保持不变）==========
    def detect_boards(self, verify_connection: bool = True) -> List[BoardInfo]
    def detect_board_by_type(self, board_type: str) -> Optional[BoardInfo]
    def generate(self, prompt: str, project_name: str, ...) -> Path
    def build(self, project_dir: Path, fqbn: str, ...) -> CompileResult
    def upload(self, project_dir: Path, fqbn: str, port: str, ...) -> UploadResult
    def monitor(self, port: str, duration: float, ...) -> MonitorResult
    
    # ========== 新增 API（Story 3-7）==========
    
    # Story 3: 开发板状态读取和验证
    def read_board_status(
        self, 
        port: str, 
        expected_output: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """读取开发板运行状态并验证
        
        Args:
            port: 串口路径
            expected_output: 期望的串口输出模式列表
            
        Returns:
            包含状态信息的字典：
            {
                "is_running": bool,
                "output": List[str],
                "matches_expected": bool,
                "matched_patterns": List[str],
                "status": "success" | "warning" | "error"
            }
        """
    
    def verify_functionality(
        self,
        project_dir: Path,
        requirement: str,
        port: Optional[str] = None
    ) -> Dict[str, Any]:
        """验证功能是否符合需求描述
        
        Args:
            project_dir: 项目目录
            requirement: 原始需求描述
            port: 串口路径（None 时自动检测）
            
        Returns:
            验证结果字典
        """
    
    # Story 4: 无硬件时的仿真验证
    def simulate(
        self,
        project_dir: Path,
        duration: float = 30.0,
        expected_output: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """运行 Wokwi 仿真
        
        Args:
            project_dir: 项目目录（需已编译）
            duration: 仿真时长（秒）
            expected_output: 期望的串口输出模式
            
        Returns:
            仿真结果字典
        """
    
    def generate_simulation_config(
        self,
        project_dir: Path,
        board_type: BoardType
    ) -> SimulationConfig:
        """生成 Wokwi 仿真配置
        
        Args:
            project_dir: 项目目录
            board_type: 板卡类型
            
        Returns:
            仿真配置对象
        """
    
    # Story 5: 自定义板子快速验证
    def register_custom_board(self, config: CustomBoardConfig) -> bool:
        """注册自定义板子配置
        
        Args:
            config: 自定义板子配置
            
        Returns:
            是否成功注册
        """
    
    def detect_custom_board(self, chip_type: str) -> Optional[CustomBoardConfig]:
        """检测自定义板子
        
        Args:
            chip_type: 芯片类型
            
        Returns:
            自定义板子配置，未找到返回 None
        """
    
    # Story 6: 模块化功能实现
    def recognize_modules(self, prompt: str) -> List[ModuleInfo]:
        """识别需求中的模块
        
        Args:
            prompt: 需求描述
            
        Returns:
            识别的模块列表
        """
    
    def generate_module_code(
        self,
        module: ModuleInfo,
        integration_context: Optional[str] = None
    ) -> str:
        """生成模块代码
        
        Args:
            module: 模块信息
            integration_context: 集成上下文（其他模块信息）
            
        Returns:
            生成的模块代码
        """
    
    # Story 7: 代码可二次开发
    def analyze_code_quality(self, project_dir: Path) -> CodeQualityMetrics:
        """分析代码质量
        
        Args:
            project_dir: 项目目录
            
        Returns:
            代码质量指标
        """
    
    def enhance_code_for_development(
        self,
        project_dir: Path,
        add_comments: bool = True,
        improve_structure: bool = True
    ) -> bool:
        """增强代码以便二次开发
        
        Args:
            project_dir: 项目目录
            add_comments: 是否添加注释
            improve_structure: 是否改进结构
            
        Returns:
            是否成功增强
        """
    
    # ========== 端到端流程 API ==========
    def end_to_end(
        self,
        prompt: str,
        project_name: str,
        auto_upload: bool = True,
        auto_verify: bool = True,
        use_simulation: bool = False
    ) -> Dict[str, Any]:
        """端到端流程：从需求到验证
        
        Args:
            prompt: 需求描述
            project_name: 项目名称
            auto_upload: 是否自动上传
            auto_verify: 是否自动验证
            use_simulation: 无板时是否使用仿真
            
        Returns:
            完整流程结果字典
        """
```

### 3.2 CLI 命令扩展

```bash
# 现有命令（保持不变）
arduino-client detect
arduino-client gen "..." <project_name> [--build] [--flash]
arduino-client build <project> --fqbn <fqbn>
arduino-client upload <project> --fqbn <fqbn> --port <port>
arduino-client monitor <port>
arduino-client interactive

# 新增命令（Story 3-7）
arduino-client status <port> [--expected <pattern>]  # Story 3
arduino-client verify <project> --requirement "..."  # Story 3
arduino-client simulate <project> [--duration <sec>] [--expected <pattern>]  # Story 4
arduino-client register-board <config.json>  # Story 5
arduino-client modules "..."  # Story 6: 识别模块
arduino-client quality <project>  # Story 7: 代码质量分析
arduino-client enhance <project> [--comments] [--structure]  # Story 7
arduino-client e2e "..." <project_name> [--simulate]  # 端到端流程
```

---

## 4. 实现顺序（依赖排序）

### Phase 1: 核心功能增强（Story 1-2 优化）
**优先级**: P0  
**依赖**: 无  
**预计工作量**: 2-3 天  
**状态**: ✅ 70% 完成（核心功能已实现）

1. **需求理解优化**
   - [x] ✅ 改进 LLM prompt，提高需求理解准确性
   - [x] ✅ 添加需求分析结果模型（RequirementAnalysis）
   - [ ] ⏳ 实现需求确认机制（可选，待实现）

2. **代码生成质量提升**
   - [x] ✅ 优化代码生成 prompt，确保包含必要库引用
   - [x] ✅ 集成需求分析结果到代码生成流程
   - [ ] ⏳ 添加代码验证逻辑（语法检查）
   - [ ] ⏳ 改进错误处理和重试机制

**已完成实现**:
- ✅ `requirement_analyzer.py` - 需求分析模块
- ✅ `models.py` - 扩展数据模型（RequirementAnalysis, BoardType, MonitorResult）
- ✅ `code_generator.py` - 优化 prompt，支持需求分析结果增强
- ✅ `client.py` - 集成需求分析到生成流程

**待完成**:
- ⏳ 代码验证逻辑（语法检查、库依赖检查）
- ⏳ 错误处理和重试机制改进
- ⏳ 单元测试（覆盖率>80%）

### Phase 2: 状态读取和验证（Story 3）
**优先级**: P0  
**依赖**: Phase 1  
**预计工作量**: 2-3 天

1. **开发板状态读取**
   - [ ] 实现 `read_board_status()` API
   - [ ] 串口输出模式匹配
   - [ ] 状态反馈机制

2. **功能验证**
   - [ ] 实现 `verify_functionality()` API
   - [ ] 需求与输出的对比逻辑
   - [ ] 验证结果报告生成

3. **CLI 命令**
   - [ ] `arduino-client status` 命令
   - [ ] `arduino-client verify` 命令

### Phase 3: 仿真支持（Story 4）
**优先级**: P1  
**依赖**: Phase 1  
**预计工作量**: 3-4 天

1. **Wokwi 集成**
   - [ ] 实现 `generate_simulation_config()` API
   - [ ] 自动生成 diagram.json 和 wokwi.toml
   - [ ] 实现 `simulate()` API

2. **仿真验证**
   - [ ] 串口输出捕获
   - [ ] 期望模式匹配
   - [ ] 仿真结果报告

3. **CLI 命令**
   - [ ] `arduino-client simulate` 命令
   - [ ] 集成到端到端流程（无板时自动使用）

### Phase 4: 自定义板子支持（Story 5）
**优先级**: P1  
**依赖**: Phase 1  
**预计工作量**: 2-3 天

1. **自定义板子配置**
   - [ ] 实现 CustomBoardConfig 模型
   - [ ] 实现 `register_custom_board()` API
   - [ ] 配置文件存储和管理

2. **板子检测和适配**
   - [ ] 实现 `detect_custom_board()` API
   - [ ] 代码生成时适配自定义引脚
   - [ ] 编译配置适配

3. **CLI 命令**
   - [ ] `arduino-client register-board` 命令

### Phase 5: 模块识别和组合（Story 6）
**优先级**: P1  
**依赖**: Phase 1  
**预计工作量**: 3-4 天

1. **模块识别**
   - [ ] 实现 ModuleInfo 模型
   - [ ] 实现 `recognize_modules()` API
   - [ ] 模块库维护（常见模块数据库）

2. **模块代码生成**
   - [ ] 实现 `generate_module_code()` API
   - [ ] 模块组合逻辑
   - [ ] 库依赖自动管理

3. **CLI 命令**
   - [ ] `arduino-client modules` 命令

### Phase 6: 代码质量提升（Story 7）
**优先级**: P2  
**依赖**: Phase 1  
**预计工作量**: 2-3 天

1. **代码质量分析**
   - [ ] 实现 CodeQualityMetrics 模型
   - [ ] 实现 `analyze_code_quality()` API
   - [ ] 代码结构分析逻辑

2. **代码增强**
   - [ ] 实现 `enhance_code_for_development()` API
   - [ ] 自动添加注释
   - [ ] 代码结构优化

3. **CLI 命令**
   - [ ] `arduino-client quality` 命令
   - [ ] `arduino-client enhance` 命令

### Phase 7: 端到端流程整合
**优先级**: P0  
**依赖**: Phase 1-3  
**预计工作量**: 2-3 天

1. **端到端 API**
   - [ ] 实现 `end_to_end()` API
   - [ ] 流程编排逻辑
   - [ ] 错误处理和回滚

2. **CLI 命令**
   - [ ] `arduino-client e2e` 命令
   - [ ] 交互式流程优化

3. **测试和文档**
   - [ ] E2E 测试用例实现
   - [ ] 使用文档更新

---

## 5. 项目结构（基于现有结构扩展）

```
arduino-client/
├── arduino_client/
│   ├── __init__.py
│   ├── client.py                    # ✅ ArduinoClient 核心 API（已扩展需求分析）
│   ├── cli.py                       # CLI 入口（待扩展命令）
│   ├── code_generator.py            # ✅ 代码生成（已优化）
│   ├── requirement_analyzer.py      # ✅ 新增：需求分析模块（已实现）
│   ├── board_detector.py            # ✅ 板卡检测（待扩展自定义板子）
│   ├── builder.py                    # ✅ 编译模块
│   ├── uploader.py                   # ✅ 上传模块
│   ├── monitor.py                    # ✅ 串口监控（待扩展状态读取）
│   ├── interactive.py                # ✅ 交互式终端
│   ├── verifier.py                   # ⏳ 新增：功能验证模块（待实现）
│   ├── simulation.py                 # ✅ 仿真模块（已有基础，待扩展）
│   ├── custom_board.py               # ⏳ 新增：自定义板子管理（待实现）
│   ├── module_recognizer.py          # ⏳ 新增：模块识别（待实现）
│   ├── code_quality.py               # ⏳ 新增：代码质量分析（待实现）
│   ├── models.py                     # ✅ 数据模型（已扩展）
│   ├── llm_config.py                 # ✅ LLM 配置
│   ├── errors.py                     # ✅ 错误定义
│   └── _paths.py                     # ✅ 路径管理
├── docs/
│   ├── LESSONS.md                    # ✅ 开发经验记录
│   └── skills/                       # ✅ Cursor Skills
├── demos/
│   └── ...
├── tests/                            # ⏳ 待创建测试目录
│   ├── test_requirement_analyzer.py  # ⏳ 新增
│   ├── test_verifier.py              # ⏳ 新增
│   ├── test_simulation.py            # ⏳ 新增
│   └── test_e2e.py                   # ⏳ 新增：E2E 测试
├── pyproject.toml                    # ✅ 项目配置
└── README.md                          # ✅ 项目说明

图例：
✅ = 已实现
⏳ = 待实现
```

---

## 6. 关键技术实现细节

### 6.1 需求分析（Story 1-2 优化）

```python
# requirement_analyzer.py

async def analyze_requirement(
    prompt: str,
    llm_client: OpenAI
) -> RequirementAnalysis:
    """分析用户需求
    
    使用 LLM 分析需求，提取：
    - 板卡类型
    - 组件列表
    - 需要的库
    - 引脚需求
    - 功能列表
    """
    system_prompt = """
    你是一个 Arduino 需求分析专家。分析用户需求，提取以下信息：
    1. 开发板类型（Uno, Nano, Pico, ESP32 等）
    2. 使用的组件（传感器、执行器等）
    3. 需要的库
    4. 引脚配置
    5. 功能描述
    
    如果需求不清晰，标记 needs_clarification=True 并提供澄清问题。
    """
    # ... LLM 调用逻辑
```

### 6.2 状态读取和验证（Story 3）

```python
# verifier.py

def read_board_status(
    port: str,
    expected_output: Optional[List[str]] = None,
    duration: float = 10.0
) -> Dict[str, Any]:
    """读取开发板状态"""
    monitor = Monitor()
    output = monitor.monitor(port, duration=duration)
    
    matches = []
    if expected_output:
        for pattern in expected_output:
            if any(pattern in line for line in output):
                matches.append(pattern)
    
    return {
        "is_running": len(output) > 0,
        "output": output,
        "matches_expected": len(matches) == len(expected_output) if expected_output else None,
        "matched_patterns": matches,
        "status": "success" if (not expected_output or len(matches) == len(expected_output)) else "warning"
    }
```

### 6.3 Wokwi 仿真集成（Story 4）

```python
# simulation.py

def generate_wokwi_config(
    project_dir: Path,
    board_type: BoardType,
    components: List[str]
) -> SimulationConfig:
    """生成 Wokwi 配置"""
    # 根据板卡类型和组件生成 diagram.json
    diagram = {
        "version": 1,
        "author": "arduino-client",
        "editor": "wokwi",
        "parts": [
            # 根据 board_type 添加开发板
            # 根据 components 添加组件
        ],
        "connections": [
            # 根据引脚映射生成连接
        ]
    }
    
    # 生成 wokwi.toml
    wokwi_toml = {
        "version": "1.0.0",
        "firmware": str(project_dir / "*.ino"),
        # ...
    }
    
    return SimulationConfig(
        project_path=project_dir,
        wokwi_config={},
        diagram_json=diagram,
        wokwi_toml=wokwi_toml
    )
```

### 6.4 模块识别（Story 6）

```python
# module_recognizer.py

MODULE_DATABASE = {
    "麦克风": ModuleInfo(
        name="麦克风",
        type="sensor",
        library="arduinoFFT",
        pins=[A0],
        example_code="..."
    ),
    "LED": ModuleInfo(
        name="LED",
        type="actuator",
        library=None,
        pins=[13],
        example_code="..."
    ),
    # ... 更多模块
}

def recognize_modules(prompt: str) -> List[ModuleInfo]:
    """识别需求中的模块"""
    recognized = []
    for keyword, module_info in MODULE_DATABASE.items():
        if keyword in prompt:
            recognized.append(module_info)
    return recognized
```

---

## 7. 测试策略

### 7.1 单元测试
- 需求分析模块测试
- 代码生成测试
- 板卡检测测试
- 验证逻辑测试

### 7.2 集成测试
- 端到端流程测试（有板）
- 端到端流程测试（无板，使用仿真）
- 自定义板子测试

### 7.3 E2E 测试
- Story 1: LED 闪烁功能
- Story 2: 闹钟功能
- Story 3: 状态验证
- Story 4: 仿真验证

---

## 8. 部署和发布

### 8.1 版本管理
- 遵循语义化版本（Semantic Versioning）
- 当前版本: 0.1.0
- 计划版本: 0.2.0（Phase 1-3 完成后）

### 8.2 发布流程
1. 代码审查
2. 单元测试通过
3. 集成测试通过
4. E2E 测试通过
5. 文档更新
6. 发布到 PyPI（可选）

---

## 9. 风险和缓解措施

| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|----------|------|
| LLM API 不稳定 | 高 | 实现重试机制，支持多个 API 提供商 | ⏳ 待实现 |
| arduino-cli 版本兼容性 | 中 | 版本锁定，测试多版本兼容性 | ✅ 已处理 |
| Wokwi CLI 依赖 | 中 | 提供清晰的安装指南，考虑备选方案 | ✅ 已处理 |
| 硬件检测不准确 | 中 | 实现多检测方法，提供手动指定选项 | ✅ 已实现 |
| 代码生成质量不稳定 | 高 | 优化 prompt，实现代码验证和修复机制 | ✅ 部分完成（prompt 已优化，验证待实现） |
| 需求分析失败 | 中 | 优雅降级到原始 prompt | ✅ 已实现 |
| 库名称不匹配 | 中 | 需要库名称映射表 | ⏳ 待实现 |
| 引脚解析不准确 | 中 | 改进引脚解析逻辑 | ⏳ 待优化 |

---

## 10. 后续优化方向

### 短期（Phase 1 完成）
1. **代码验证和测试**
   - 实现代码语法检查
   - 实现库依赖验证
   - 编写单元测试（覆盖率>80%）
   - 改进错误处理和重试机制

### 中期（Phase 2-4）
2. **功能完善**
   - 状态读取和验证（Story 3）
   - 仿真支持增强（Story 4）
   - 自定义板子支持（Story 5）

### 长期（Phase 5-7）
3. **性能优化**
   - 代码生成缓存
   - 并行编译支持
   - 需求分析结果缓存

4. **用户体验**
   - 更友好的错误提示
   - 进度显示
   - 交互式需求引导
   - 需求确认机制

5. **功能扩展**
   - 模块识别和组合（Story 6）
   - 代码质量提升（Story 7）
   - 支持更多开发板
   - 支持更多仿真平台
   - 代码版本管理

6. **社区支持**
   - 模块库社区贡献
   - 自定义板子配置共享
   - 库名称映射表维护

---

## 11. 架构设计更新记录

### 2026-02-20 架构审查和优化
**基于**: PRD 文档和 Phase 1 实现状态

**更新内容**:
1. ✅ 标记 Phase 1 已完成功能（需求分析模块）
2. ✅ 更新项目结构，标注实现状态
3. ✅ 更新风险列表，标注缓解措施状态
4. ✅ 细化后续优化方向，按优先级分类

**关键决策确认**:
- ✅ LLM API 用于需求分析和代码生成（已验证可行）
- ✅ 需求分析失败时优雅降级（已实现）
- ✅ 使用 Pydantic 进行数据验证（已实现）
- ⏳ 代码验证逻辑待实现（Phase 1 剩余工作）

**下一步重点**:
1. 完成 Phase 1 剩余工作（代码验证、测试）
2. 开始 Phase 2（状态读取和验证）
3. 完善端到端流程整合
