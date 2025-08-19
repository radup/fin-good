# Dr. Sigmund Spend - Technical Architecture

**Document Type:** Technical Architecture Specification  
**Version:** 1.0  
**Dependencies:** Local LLM Integration, Function Calling/MCP, Financial Data APIs  

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                          │
├─────────────────────────────────────────────────────────────────┤
│  Chat Interface  │  Financial Dashboard  │  Visualization     │
│  - Conversation  │  - Metrics Display    │  - Charts/Graphs   │
│  - Dr. Sigmund   │  - Real-time Data     │  - Scenario Viz    │
│  - Voice/Text    │  - Historical Trends  │  - Forecasts       │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LLM ORCHESTRATION LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│  Dr. Sigmund Personality Engine    │    Function Router        │
│  - Character consistency           │    - Intent Classification │
│  - German accent processing        │    - Tool Selection       │
│  - Therapeutic tone management     │    - Parameter Extraction │
│  - Context memory management       │    - Response Formatting  │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL LLM ENGINE                            │
├─────────────────────────────────────────────────────────────────┤
│   Ollama Runtime Environment                                   │
│   ├── Llama3.1 8B (Primary)     ├── Mistral 7B (Fallback)    │
│   ├── Custom Financial LoRA     ├── German Accent LoRA       │
│   ├── Function Calling Support  ├── Context Window: 128k     │
│   └── Local GPU/CPU Optimization └── Response Streaming      │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FUNCTION CALLING LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  MCP Protocol Implementation       │    Function Registry      │
│  - Tool Discovery                  │    - Financial Tools      │
│  - Parameter Validation            │    - ML Model Tools       │
│  - Response Handling               │    - Scenario Tools       │
│  - Error Recovery                  │    - Data Query Tools     │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FINANCIAL TOOLS LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│ Data Query Tools  │  ML Model Tools    │   Scenario Tools      │
│ - Transaction API │  - Categorization  │   - What-if Analysis  │
│ - Account Balance │  - Forecasting     │   - Budget Simulation │
│ - Category Stats  │  - Pattern Detect  │   - Goal Planning     │
│ - Historical Data │  - Anomaly Detect  │   - Risk Assessment   │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXISTING BACKEND APIS                        │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Endpoints  │  ML Models         │   Database Layer    │
│  - /transactions    │  - Forecasting     │   - PostgreSQL     │
│  - /analytics       │  - Categorization  │   - Redis Cache    │
│  - /patterns        │  - Duplicates      │   - Vector Store   │
│  - /forecasting     │  - Bulk Operations │   - Time Series    │
└─────────────────────────────────────────────────────────────────┘
```

## 🧠 LLM Integration Strategy

### **Local LLM Setup (Ollama)**

**Primary Model: Llama3.1 8B**
- **Context Window**: 128k tokens
- **Fine-tuning**: Custom LoRA for financial domain
- **Character**: German accent and therapeutic personality LoRA
- **Function Calling**: Native support with structured outputs

**Fallback Model: Mistral 7B**
- **Use Case**: Backup when Llama3.1 unavailable
- **Performance**: Faster inference, smaller memory footprint
- **Capabilities**: Basic financial queries and conversation

**Model Serving Infrastructure:**
```python
# Ollama Configuration
{
    "model": "llama3.1:8b-instruct-q8_0",
    "keep_alive": "5m",
    "stream": true,
    "options": {
        "temperature": 0.1,  # Low for consistent financial advice
        "top_p": 0.9,
        "num_ctx": 128000,   # Full context window
        "num_predict": 2048  # Max response tokens
    }
}
```

## 🛠️ Function Calling vs MCP Decision Matrix

### **Recommended Approach: MCP (Model Context Protocol)**

**Advantages:**
- **Standardized Protocol**: Industry standard for LLM-tool integration
- **Dynamic Discovery**: Tools can be discovered at runtime
- **Extensibility**: Easy to add new financial tools
- **Type Safety**: Structured parameter validation
- **Error Handling**: Robust error recovery mechanisms

**Implementation:**
```python
# MCP Financial Tools Server
class FinancialToolsServer:
    def __init__(self):
        self.tools = {
            "get_account_balance": GetAccountBalanceTool(),
            "query_transactions": QueryTransactionsTool(),
            "forecast_cashflow": ForecastCashflowTool(),
            "analyze_spending": AnalyzeSpendingTool(),
            "simulate_scenario": SimulateScenarioTool()
        }
    
    async def execute_tool(self, tool_name: str, parameters: dict):
        tool = self.tools[tool_name]
        return await tool.execute(parameters)
```

## 🎭 Dr. Sigmund Personality Engine

### **Character Consistency Framework**

**Personality Traits Implementation:**
```python
class DrSigmundPersonality:
    def __init__(self):
        self.accent_patterns = {
            "th": "z",      # "the" -> "ze"
            "w": "v",       # "what" -> "vhat"
            "this": "zis",  # "this" -> "zis"
        }
        
        self.therapeutic_phrases = [
            "Let me help you understand...",
            "Zis is perfectly normal...",
            "Ve can work through zis together...",
            "Your financial wellness is important..."
        ]
        
        self.german_expressions = [
            "Ach, I see...",
            "Ja, zat makes sense...",
            "Mein friend...",
            "Vunderbar!"
        ]
    
    def apply_personality(self, response: str) -> str:
        # Apply German accent patterns
        for english, german in self.accent_patterns.items():
            response = response.replace(english, german)
        
        # Add therapeutic framing
        if self.is_financial_advice(response):
            response = self.add_therapeutic_context(response)
            
        return response
```

### **Context Memory Management**

**Conversation History:**
- **Short-term Memory**: Last 10 exchanges (stored in Redis)
- **Session Context**: Current financial focus area
- **Long-term Patterns**: User's recurring financial concerns
- **Therapeutic Progress**: Track user's financial wellness journey

## 📊 Financial Data Integration

### **Available Financial Tools**

**1. Account & Transaction Tools**
```python
@mcp_tool
async def get_account_balance(user_id: int, account_types: List[str] = None):
    """Get current account balances for user"""
    
@mcp_tool  
async def query_transactions(
    user_id: int, 
    date_range: DateRange,
    categories: List[str] = None,
    amount_range: AmountRange = None
):
    """Query transactions with flexible filters"""
```

**2. Analytics & Insights Tools**
```python
@mcp_tool
async def analyze_spending_patterns(user_id: int, period: str = "3months"):
    """Analyze spending patterns and trends"""
    
@mcp_tool
async def detect_financial_anomalies(user_id: int, sensitivity: float = 0.8):
    """Detect unusual financial patterns"""
```

**3. Forecasting & Simulation Tools**
```python
@mcp_tool
async def forecast_cashflow(
    user_id: int, 
    horizon_months: int = 6,
    scenario: str = "base"
):
    """Generate cash flow forecasts"""
    
@mcp_tool
async def simulate_financial_scenario(
    user_id: int,
    changes: Dict[str, float],  # e.g., {"rent": -200, "income": 500}
    duration_months: int = 12
):
    """Simulate what-if financial scenarios"""
```

## 🔄 Conversation Flow Architecture

### **Intent Classification Pipeline**

```python
class ConversationManager:
    def __init__(self):
        self.intent_classifier = FinancialIntentClassifier()
        self.tool_router = ToolRouter()
        self.response_formatter = DrSigmundFormatter()
    
    async def process_user_message(self, message: str, user_context: dict):
        # 1. Classify user intent
        intent = await self.intent_classifier.classify(message, user_context)
        
        # 2. Route to appropriate tools
        tools_needed = self.tool_router.select_tools(intent)
        
        # 3. Execute tools and gather data
        tool_results = await self.execute_tools(tools_needed, intent.parameters)
        
        # 4. Generate LLM response with data
        llm_response = await self.generate_response(message, tool_results, user_context)
        
        # 5. Apply Dr. Sigmund personality
        final_response = self.response_formatter.format(llm_response)
        
        return final_response
```

### **Sample Conversation Flows**

**User Query:** "How much did I spend on coffee last month?"

**Processing Flow:**
1. **Intent**: Query spending by category and timeframe
2. **Tools**: `query_transactions(categories=["Coffee", "Café"], date_range=last_month)`
3. **Data**: $127.50 across 23 transactions
4. **LLM Response**: Raw financial analysis
5. **Dr. Sigmund**: "Ach, I see you have ze coffee passion, ja? Last month you spent $127.50 on coffee across 23 visits - zat's about $4.10 per day. For someone who needs zair caffeine therapy, zis is quite reasonable! Perhaps ve can find vays to enjoy your coffee ritual vhile being mindful of ze budget, mein friend."

## 🚀 Performance Optimization

### **Local LLM Optimization**

**Hardware Requirements:**
- **Minimum**: 16GB RAM, 8-core CPU, 6GB GPU VRAM
- **Recommended**: 32GB RAM, 12-core CPU, 12GB GPU VRAM
- **Optimal**: 64GB RAM, 16-core CPU, 24GB GPU VRAM

**Inference Optimization:**
```python
# Ollama Performance Tuning
ollama_config = {
    "num_thread": os.cpu_count(),
    "num_gpu": 1,
    "use_mmap": True,
    "use_mlock": True,
    "numa": True
}
```

**Response Streaming:**
- **Real-time Responses**: Stream tokens as generated
- **Typing Indicators**: Show Dr. Sigmund "thinking"
- **Partial Updates**: Display financial data while LLM processes

### **Caching Strategy**

**Multi-Layer Caching:**
1. **LLM Response Cache**: Common financial questions (Redis, 1 hour TTL)
2. **Financial Data Cache**: Account balances, recent transactions (Redis, 5 min TTL)
3. **ML Model Cache**: Forecasts, pattern analysis (Redis, 30 min TTL)
4. **Session Cache**: Conversation context (Redis, session lifetime)

## 🔒 Security & Privacy

### **Local Processing Benefits**

**Data Privacy:**
- **No Cloud Transmission**: All LLM processing happens locally
- **GDPR Compliance**: User data never leaves their environment
- **Financial Privacy**: Sensitive financial data stays on-premise
- **Audit Trail**: Complete local logging of all interactions

**Security Measures:**
```python
class SecurityManager:
    def sanitize_financial_data(self, data: dict) -> dict:
        """Remove PII before LLM processing"""
        
    def encrypt_conversation_history(self, conversation: list) -> bytes:
        """Encrypt stored conversation history"""
        
    def validate_tool_parameters(self, tool_call: dict) -> bool:
        """Validate all tool calls for security"""
```

## 📈 Monitoring & Analytics

### **System Monitoring**

**Performance Metrics:**
- **LLM Response Time**: Target <3 seconds for simple queries
- **Tool Execution Time**: Target <1 second for data queries
- **Conversation Quality**: User satisfaction ratings
- **Error Rates**: Tool failures, LLM hallucinations

**Business Metrics:**
- **User Engagement**: Questions per session, session length
- **Feature Usage**: Most used financial tools
- **Therapeutic Effectiveness**: User financial stress reduction
- **Accuracy**: Financial advice quality and relevance

---

*Dr. Sigmund Spend Technical Architecture - Created August 19, 2025*