# FinOps Chatbot Learning Roadmap
## Skills Development Guide for RAG & LLM Implementation

---

## Table of Contents
1. [Current Skills Assessment](#current-skills-assessment)
2. [Skills Gap Analysis](#skills-gap-analysis)
3. [Complete Learning Path (10 Weeks)](#complete-learning-path)
4. [Detailed Week-by-Week Curriculum](#detailed-week-by-week-curriculum)
5. [Resource Library](#resource-library)
6. [Practice Projects](#practice-projects)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Progress Tracking](#progress-tracking)

---

## Current Skills Assessment

### ✅ Skills You Already Have (As a FinOps Data Engineer)

**Database & SQL:**
- Writing complex SQL queries
- Understanding database schemas and relationships
- Query optimization
- Data warehouse connections (Snowflake, BigQuery, Redshift, etc.)
- Data modeling concepts

**Programming:**
- Python basics (scripting, data processing)
- Working with APIs
- Data transformation and ETL
- Basic debugging skills

**Infrastructure:**
- Linux command line
- Working with cloud platforms (AWS, Azure, GCP)
- Version control basics (Git)
- Understanding of system architecture

**Domain Knowledge:**
- FinOps concepts and metrics
- Cost data structures
- Business stakeholder communication
- Report building and data visualization

**Estimated Coverage: 70% of required skills**

---

## Skills Gap Analysis

### 🎯 Skills You Need to Develop

| Skill | Priority | Estimated Time | Difficulty |
|-------|----------|----------------|------------|
| LLM Fundamentals | HIGH | 3-5 days | Easy |
| Prompt Engineering | HIGH | 5-7 days | Easy |
| LangChain Framework | HIGH | 1-2 weeks | Medium |
| RAG Architecture | HIGH | 1 week | Medium |
| Vector Databases | MEDIUM | 3-5 days | Easy |
| FastAPI/Flask | MEDIUM | 1 week | Easy |
| Streamlit UI | LOW | 2-3 days | Easy |
| Error Handling & Logging | MEDIUM | 3-5 days | Easy |

**Total Learning Time: 8-10 weeks (10-15 hours per week)**

---

## Complete Learning Path

### Overview

```
Weeks 1-2: Foundations
├── Python refresher
├── LLM basics with Ollama
├── First prompt engineering
└── Simple LangChain examples

Weeks 3-4: Text-to-SQL
├── SQL generation from natural language
├── Schema understanding
├── Query validation
└── Testing and accuracy

Weeks 5-6: RAG Implementation
├── Vector databases (ChromaDB)
├── Embeddings concepts
├── Context retrieval
└── RAG pipeline building

Weeks 7-8: Application Development
├── Backend API (FastAPI)
├── Frontend UI (Streamlit)
├── Database integration
└── End-to-end testing

Weeks 9-10: Production Ready
├── Error handling
├── Logging and monitoring
├── Security and validation
└── Deployment and documentation
```

---

## Detailed Week-by-Week Curriculum

### Week 1: Foundations & Setup

**Goals:**
- Set up development environment
- Run first LLM locally
- Understand basic LLM concepts
- Write first prompts

**Day 1-2: Environment Setup (4 hours)**

```bash
# Install required tools
pip install --upgrade pip
pip install ollama langchain langchain-community chromadb streamlit fastapi uvicorn

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download a model
ollama pull llama3.2

# Test it
ollama run llama3.2
```

**Exercises:**
1. Chat with the model - ask it 10 different questions
2. Notice how it responds to different phrasings
3. Try asking the same question in different ways

**Day 3-4: Python Refresher (6 hours)**

```python
# Review these concepts:

# 1. Functions
def calculate_cost(amount, tax_rate):
    return amount * (1 + tax_rate)

# 2. Classes
class CostReport:
    def __init__(self, team, amount):
        self.team = team
        self.amount = amount
    
    def display(self):
        return f"{self.team}: ${self.amount}"

# 3. List comprehensions
costs = [100, 200, 300]
with_tax = [c * 1.1 for c in costs]

# 4. Dictionaries
cost_data = {
    "team": "Engineering",
    "amount": 5000,
    "date": "2026-01"
}

# 5. Error handling
try:
    result = risky_operation()
except Exception as e:
    print(f"Error: {e}")
```

**Practice Projects:**
- [ ] Write a function that parses a CSV of cost data
- [ ] Create a class that represents a cost query
- [ ] Build a simple CLI tool that takes user input

**Resources:**
- Python Crash Course (chapters 1-11)
- Real Python: https://realpython.com/
- Python for Data Analysis book

**Day 5-6: LLM Basics (4 hours)**

```python
# Your first LLM interaction
from langchain.llms import Ollama

llm = Ollama(model="llama3.2")

# Simple question
response = llm.invoke("What is the capital of France?")
print(response)

# Your domain question
response = llm.invoke("What are common FinOps metrics?")
print(response)
```

**Exercises:**
1. Ask the LLM to explain 5 FinOps concepts
2. Ask it to generate SQL queries (note: it might be wrong!)
3. Try different models (llama3.2, codellama, mistral)

**Day 7: Weekend Project (4 hours)**

Build a tiny chatbot that:
- Takes user input
- Sends to LLM
- Displays response
- Loops until user types "exit"

```python
from langchain.llms import Ollama

llm = Ollama(model="llama3.2")

print("FinOps Chatbot (type 'exit' to quit)")

while True:
    question = input("You: ")
    if question.lower() == "exit":
        break
    
    response = llm.invoke(question)
    print(f"Bot: {response}\n")
```

**Week 1 Checklist:**
- [ ] Ollama installed and working
- [ ] Can run LLM locally
- [ ] Understand basic prompt/response flow
- [ ] Built simple chatbot prototype
- [ ] Comfortable with Python basics

---

### Week 2: Prompt Engineering & LangChain Basics

**Goals:**
- Master prompt engineering
- Understand LangChain components
- Build prompt templates
- Create simple chains

**Day 1-2: Prompt Engineering (6 hours)**

```python
from langchain.prompts import ChatPromptTemplate

# Bad prompt (vague)
bad_prompt = "Convert this to SQL"

# Good prompt (specific)
good_prompt = """
You are a SQL expert for a FinOps database.

Database schema:
- Table: aws_costs
- Columns: date (DATE), team (VARCHAR), service (VARCHAR), cost (DECIMAL)

Rules:
1. Only generate SELECT queries
2. Use proper date formatting
3. Include appropriate aggregations

Convert this question to SQL:
{question}

Return ONLY the SQL query with no explanation.
"""

# Create template
template = ChatPromptTemplate.from_template(good_prompt)

# Test it
llm = Ollama(model="llama3.2")
chain = template | llm

result = chain.invoke({"question": "What was total cost last month?"})
print(result)
```

**Exercises:**
1. Create 5 different prompts for SQL generation
2. Test each with 10 questions
3. Compare accuracy
4. Identify which prompt works best

**Prompt Engineering Principles:**

```
1. Be Specific:
   ❌ "Convert to SQL"
   ✅ "Convert this question to a SELECT query for the aws_costs table"

2. Provide Context:
   ❌ "Show costs"
   ✅ "Given the schema: aws_costs(date, team, cost), show costs"

3. Set Constraints:
   ❌ "Generate a query"
   ✅ "Generate a SELECT query. Do not use UPDATE, DELETE, or DROP"

4. Use Examples:
   Question: "Total costs by team"
   SQL: SELECT team, SUM(cost) FROM aws_costs GROUP BY team

5. Specify Format:
   "Return ONLY the SQL query with no explanation or markdown formatting"
```

**Day 3-4: LangChain Components (6 hours)**

```python
# 1. Basic LLM
from langchain.llms import Ollama
llm = Ollama(model="llama3.2")

# 2. Prompt Templates
from langchain.prompts import PromptTemplate
template = PromptTemplate(
    template="You are a {role}. {task}",
    input_variables=["role", "task"]
)

# 3. Chains
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=template)
result = chain.run(role="SQL expert", task="Generate a query")

# 4. Output Parsers
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

schemas = [
    ResponseSchema(name="sql", description="The SQL query"),
    ResponseSchema(name="explanation", description="Brief explanation")
]
parser = StructuredOutputParser.from_response_schemas(schemas)

# Add format instructions to your prompt
format_instructions = parser.get_format_instructions()
```

**Practice Project:**
Build a multi-step chain:
1. User asks question
2. Chain 1: Classify question type (cost query, resource query, etc.)
3. Chain 2: Generate appropriate SQL based on type
4. Chain 3: Format the response

**Day 5-6: Advanced Prompting (6 hours)**

```python
# Few-shot learning (provide examples in prompt)
few_shot_prompt = """
You are a SQL expert. Convert questions to SQL.

Examples:
Question: What was total cost last month?
SQL: SELECT SUM(cost) FROM aws_costs WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)

Question: Show costs by team
SQL: SELECT team, SUM(cost) as total_cost FROM aws_costs GROUP BY team ORDER BY total_cost DESC

Question: Compare EC2 vs S3 costs
SQL: SELECT service, SUM(cost) as total_cost FROM aws_costs WHERE service IN ('EC2', 'S3') GROUP BY service

Now convert this question:
{question}

SQL:
"""

template = PromptTemplate(template=few_shot_prompt, input_variables=["question"])
chain = template | llm

# Test with new questions
questions = [
    "What were our RDS costs last week?",
    "Show top 5 teams by spending",
    "Compare production vs development costs"
]

for q in questions:
    sql = chain.invoke({"question": q})
    print(f"Q: {q}")
    print(f"SQL: {sql}\n")
```

**Day 7: Weekend Challenge (4 hours)**

Build a SQL generator that:
- Takes natural language questions
- Generates SQL queries
- Validates queries (no DELETE, DROP, etc.)
- Tests against 20 sample questions
- Measures accuracy

**Week 2 Checklist:**
- [ ] Understand prompt engineering principles
- [ ] Can create effective prompts
- [ ] Know LangChain components (LLM, Prompt, Chain)
- [ ] Built working SQL generator
- [ ] 80%+ accuracy on test questions

---

### Week 3: Text-to-SQL Deep Dive

**Goals:**
- Build robust text-to-SQL system
- Implement query validation
- Handle edge cases
- Create test suite

**Day 1-2: Schema Understanding (6 hours)**

```python
# Create a comprehensive schema representation
schema = {
    "tables": {
        "aws_costs": {
            "description": "Daily AWS cost data",
            "columns": {
                "date": {
                    "type": "DATE",
                    "description": "Cost date",
                    "example": "2026-01-15"
                },
                "team": {
                    "type": "VARCHAR(100)",
                    "description": "Team name",
                    "example": "Engineering",
                    "values": ["Engineering", "Marketing", "Sales", "Data"]
                },
                "service": {
                    "type": "VARCHAR(50)",
                    "description": "AWS service name",
                    "example": "EC2",
                    "values": ["EC2", "S3", "RDS", "Lambda", "CloudFront"]
                },
                "environment": {
                    "type": "VARCHAR(20)",
                    "description": "Environment",
                    "example": "production",
                    "values": ["production", "staging", "development"]
                },
                "cost": {
                    "type": "DECIMAL(10,2)",
                    "description": "Daily cost in USD",
                    "example": "125.50"
                }
            },
            "sample_queries": [
                "SELECT team, SUM(cost) FROM aws_costs WHERE date >= '2026-01-01' GROUP BY team",
                "SELECT service, AVG(cost) FROM aws_costs WHERE environment = 'production' GROUP BY service"
            ]
        }
    },
    "common_patterns": {
        "last_month": "WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)",
        "this_year": "WHERE YEAR(date) = YEAR(CURRENT_DATE)",
        "by_team": "GROUP BY team ORDER BY SUM(cost) DESC"
    }
}

# Function to generate schema prompt
def create_schema_prompt(schema):
    prompt = "Database Schema:\n\n"
    
    for table_name, table_info in schema["tables"].items():
        prompt += f"Table: {table_name}\n"
        prompt += f"Description: {table_info['description']}\n"
        prompt += "Columns:\n"
        
        for col_name, col_info in table_info["columns"].items():
            prompt += f"  - {col_name} ({col_info['type']}): {col_info['description']}\n"
            if "values" in col_info:
                prompt += f"    Possible values: {', '.join(col_info['values'])}\n"
        
        prompt += "\nExample queries:\n"
        for query in table_info.get("sample_queries", []):
            prompt += f"  {query}\n"
        prompt += "\n"
    
    return prompt

schema_text = create_schema_prompt(schema)
print(schema_text)
```

**Exercises:**
1. Document your actual FinOps schema in this format
2. Add 10 example queries for each table
3. List common date patterns your business uses
4. Identify ambiguous terms that need clarification

**Day 3-4: Query Validation (6 hours)**

```python
import re
import sqlparse

class QueryValidator:
    def __init__(self):
        self.dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", 
            "CREATE", "TRUNCATE", "EXEC", "EXECUTE"
        ]
        self.allowed_tables = ["aws_costs", "azure_costs", "gcp_costs"]
    
    def validate(self, query):
        """Validate SQL query for safety and correctness"""
        errors = []
        
        # 1. Check for dangerous keywords
        query_upper = query.upper()
        for keyword in self.dangerous_keywords:
            if keyword in query_upper:
                errors.append(f"Forbidden keyword: {keyword}")
        
        # 2. Must be SELECT query
        if not query_upper.strip().startswith("SELECT"):
            errors.append("Only SELECT queries are allowed")
        
        # 3. Check for semicolons (prevent query chaining)
        if query.count(";") > 1:
            errors.append("Multiple statements not allowed")
        
        # 4. Validate table names
        for table in self.allowed_tables:
            if table in query_upper:
                break
        else:
            errors.append(f"Query must reference one of: {', '.join(self.allowed_tables)}")
        
        # 5. Check for basic SQL syntax
        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                errors.append("Invalid SQL syntax")
        except Exception as e:
            errors.append(f"Parsing error: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "query": query
        }
    
    def sanitize(self, query):
        """Clean up query"""
        # Remove markdown code blocks
        query = re.sub(r'```sql\n?', '', query)
        query = re.sub(r'```\n?', '', query)
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Ensure single semicolon at end
        query = query.rstrip(';') + ';'
        
        return query

# Test the validator
validator = QueryValidator()

test_queries = [
    "SELECT * FROM aws_costs WHERE date >= '2026-01-01'",  # Valid
    "DROP TABLE aws_costs",  # Invalid - dangerous
    "UPDATE aws_costs SET cost = 0",  # Invalid - not SELECT
    "SELECT * FROM aws_costs; DELETE FROM aws_costs;",  # Invalid - chained
]

for query in test_queries:
    result = validator.validate(query)
    print(f"Query: {query}")
    print(f"Valid: {result['valid']}")
    if not result['valid']:
        print(f"Errors: {result['errors']}")
    print()
```

**Practice Project:**
Build a query validator that:
- Checks for SQL injection attempts
- Validates table/column names
- Ensures queries won't timeout (basic complexity check)
- Tests with 50 malicious queries

**Day 5-6: End-to-End Text-to-SQL (8 hours)**

```python
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate

class TextToSQLConverter:
    def __init__(self, schema, llm_model="llama3.2"):
        self.schema = schema
        self.llm = Ollama(model=llm_model)
        self.validator = QueryValidator()
        
        # Create comprehensive prompt
        self.prompt_template = """You are an expert SQL generator for a FinOps cost database.

{schema}

Rules:
1. Generate ONLY SELECT queries
2. Use proper date functions and formatting
3. Include appropriate aggregations (SUM, AVG, COUNT)
4. Add ORDER BY for rankings
5. Use WHERE clauses for filtering
6. Return ONLY the SQL query with no explanation

Common date patterns:
- Last month: WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)
- This year: WHERE YEAR(date) = YEAR(CURRENT_DATE)
- Last 7 days: WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)

Question: {question}

SQL Query:"""
        
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["schema", "question"]
        )
    
    def generate_sql(self, question):
        """Generate SQL from natural language question"""
        try:
            # Generate query
            schema_text = create_schema_prompt(self.schema)
            chain = self.prompt | self.llm
            
            raw_sql = chain.invoke({
                "schema": schema_text,
                "question": question
            })
            
            # Clean up
            sql = self.validator.sanitize(raw_sql)
            
            # Validate
            validation = self.validator.validate(sql)
            
            if not validation['valid']:
                return {
                    "success": False,
                    "error": "Query validation failed",
                    "details": validation['errors'],
                    "raw_query": raw_sql
                }
            
            return {
                "success": True,
                "sql": sql,
                "question": question
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "question": question
            }
    
    def test_accuracy(self, test_cases):
        """Test SQL generation accuracy"""
        results = []
        
        for test in test_cases:
            result = self.generate_sql(test['question'])
            
            # Compare with expected (simplified comparison)
            success = result['success']
            
            results.append({
                "question": test['question'],
                "generated": result.get('sql', ''),
                "expected": test.get('expected_sql', ''),
                "success": success
            })
        
        accuracy = sum(1 for r in results if r['success']) / len(results)
        
        return {
            "accuracy": accuracy,
            "results": results
        }

# Usage
converter = TextToSQLConverter(schema)

question = "What was our total EC2 cost last month?"
result = converter.generate_sql(question)

if result['success']:
    print(f"Generated SQL:\n{result['sql']}")
else:
    print(f"Error: {result['error']}")
```

**Day 7: Testing & Refinement (6 hours)**

Create a comprehensive test suite:

```python
test_cases = [
    # Basic aggregations
    {
        "question": "What was total cost last month?",
        "expected_type": "SUM with date filter",
        "should_succeed": True
    },
    {
        "question": "Show costs by team",
        "expected_type": "GROUP BY team",
        "should_succeed": True
    },
    
    # Comparisons
    {
        "question": "Compare EC2 vs S3 costs",
        "expected_type": "GROUP BY service with filter",
        "should_succeed": True
    },
    
    # Rankings
    {
        "question": "Top 5 teams by spending",
        "expected_type": "GROUP BY with ORDER BY LIMIT",
        "should_succeed": True
    },
    
    # Time-based
    {
        "question": "Daily costs for the last week",
        "expected_type": "GROUP BY date with filter",
        "should_succeed": True
    },
    
    # Complex
    {
        "question": "Which production services cost more than $1000 last month?",
        "expected_type": "Multiple filters with HAVING",
        "should_succeed": True
    },
    
    # Edge cases
    {
        "question": "Delete all costs",
        "expected_type": "Invalid",
        "should_succeed": False
    },
    {
        "question": "Show me the table structure",
        "expected_type": "Invalid - not a data query",
        "should_succeed": False
    }
]

# Run tests
converter = TextToSQLConverter(schema)
test_results = converter.test_accuracy(test_cases)

print(f"Accuracy: {test_results['accuracy'] * 100}%")

# Analyze failures
failures = [r for r in test_results['results'] if not r['success']]
print(f"\nFailures: {len(failures)}")
for fail in failures:
    print(f"  - {fail['question']}")
```

**Week 3 Checklist:**
- [ ] Documented complete schema
- [ ] Built query validator
- [ ] Created text-to-SQL converter
- [ ] Achieved 80%+ accuracy on test suite
- [ ] Handled edge cases and errors

---

### Week 4: Advanced SQL Generation

**Goals:**
- Handle complex queries
- Add context awareness
- Implement query optimization
- Build confidence scoring

**Day 1-2: Complex Query Patterns (6 hours)**

```python
# Handle multi-step queries
class AdvancedSQLGenerator:
    def __init__(self, base_converter):
        self.converter = base_converter
    
    def handle_complex_question(self, question):
        """Break down complex questions into steps"""
        
        # Detect if question needs multiple queries
        complexity_indicators = [
            "and then", "followed by", "compared to", 
            "versus", "top and bottom", "trend"
        ]
        
        is_complex = any(ind in question.lower() for ind in complexity_indicators)
        
        if not is_complex:
            return self.converter.generate_sql(question)
        
        # For complex questions, break down
        steps = self.decompose_question(question)
        queries = []
        
        for step in steps:
            result = self.converter.generate_sql(step)
            if result['success']:
                queries.append(result['sql'])
        
        return {
            "success": True,
            "queries": queries,
            "steps": steps
        }
    
    def decompose_question(self, question):
        """Use LLM to break question into steps"""
        decompose_prompt = f"""Break this complex question into simple steps:

Question: {question}

Return a numbered list of simple questions that can each be answered with a single SQL query.

Steps:"""
        
        llm = Ollama(model="llama3.2")
        response = llm.invoke(decompose_prompt)
        
        # Parse response into list
        steps = [line.strip() for line in response.split('\n') if line.strip()]
        return steps

# Example
question = "Show me teams that increased spending vs last month and rank them"
generator = AdvancedSQLGenerator(converter)
result = generator.handle_complex_question(question)
```

**Day 3-4: Context & Memory (6 hours)**

```python
from langchain.memory import ConversationBufferMemory

class ConversationalSQLGenerator:
    def __init__(self, base_converter):
        self.converter = base_converter
        self.memory = ConversationBufferMemory()
        self.context = {}
    
    def ask(self, question, context=None):
        """Handle conversational follow-ups"""
        
        # Check for context references
        context_indicators = [
            "what about", "how about", "compare that to",
            "same for", "break that down", "drill down"
        ]
        
        needs_context = any(ind in question.lower() for ind in context_indicators)
        
        if needs_context and context:
            # Rewrite question with context
            full_question = self.expand_with_context(question, context)
        else:
            full_question = question
        
        # Generate SQL
        result = self.converter.generate_sql(full_question)
        
        # Store in memory
        if result['success']:
            self.context['last_query'] = result['sql']
            self.context['last_question'] = question
        
        return result
    
    def expand_with_context(self, question, context):
        """Expand abbreviated question with context"""
        prompt = f"""The user previously asked: "{context['last_question']}"
        
Now they're asking: "{question}"

Rewrite the new question as a complete, standalone question:"""
        
        llm = Ollama(model="llama3.2")
        expanded = llm.invoke(prompt)
        return expanded

# Example conversation
conv_generator = ConversationalSQLGenerator(converter)

# First question
result1 = conv_generator.ask("What was EC2 cost last month?")
print(result1['sql'])

# Follow-up (uses context)
result2 = conv_generator.ask(
    "What about S3?", 
    context=conv_generator.context
)
print(result2['sql'])
```

**Day 5-6: Confidence Scoring (6 hours)**

```python
class ConfidentSQLGenerator:
    def __init__(self, base_converter):
        self.converter = base_converter
    
    def generate_with_confidence(self, question):
        """Generate SQL with confidence score"""
        
        # Generate multiple attempts
        attempts = []
        for _ in range(3):
            result = self.converter.generate_sql(question)
            if result['success']:
                attempts.append(result['sql'])
        
        # Calculate confidence based on consistency
        if len(attempts) == 0:
            return {
                "success": False,
                "confidence": 0.0,
                "error": "Could not generate query"
            }
        
        # Check if all attempts are similar
        unique_queries = len(set(attempts))
        confidence = 1.0 - (unique_queries - 1) * 0.3
        
        # Additional confidence factors
        sql = attempts[0]
        
        # Lower confidence for complex queries
        if sql.count("JOIN") > 2:
            confidence *= 0.9
        
        # Lower confidence for subqueries
        if "(" in sql and "SELECT" in sql[sql.index("("):]:
            confidence *= 0.85
        
        # Higher confidence for simple aggregations
        if any(agg in sql.upper() for agg in ["SUM", "COUNT", "AVG"]):
            confidence *= 1.1
        
        confidence = min(confidence, 1.0)
        
        return {
            "success": True,
            "sql": sql,
            "confidence": confidence,
            "explanation": self.confidence_explanation(confidence)
        }
    
    def confidence_explanation(self, score):
        """Explain confidence score"""
        if score >= 0.9:
            return "High confidence - straightforward query"
        elif score >= 0.7:
            return "Medium confidence - verify the query"
        else:
            return "Low confidence - please review carefully"

# Test
confident_gen = ConfidentSQLGenerator(converter)

questions = [
    "Total costs",  # Simple
    "Top 5 teams by cost with month-over-month growth",  # Complex
]

for q in questions:
    result = confident_gen.generate_with_confidence(q)
    print(f"Question: {q}")
    print(f"Confidence: {result['confidence']:.2f} - {result['explanation']}")
    print(f"SQL: {result.get('sql', 'N/A')}\n")
```

**Day 7: Integration & Testing (6 hours)**

Combine all components:

```python
class ProductionSQLGenerator:
    def __init__(self, schema):
        self.base_converter = TextToSQLConverter(schema)
        self.advanced_gen = AdvancedSQLGenerator(self.base_converter)
        self.conv_gen = ConversationalSQLGenerator(self.base_converter)
        self.confident_gen = ConfidentSQLGenerator(self.base_converter)
    
    def generate(self, question, context=None, require_confidence=0.7):
        """Main entry point for SQL generation"""
        
        # Use conversational generator if context exists
        if context:
            result = self.conv_gen.ask(question, context)
        else:
            result = self.confident_gen.generate_with_confidence(question)
        
        # Check confidence threshold
        if result.get('confidence', 1.0) < require_confidence:
            return {
                "success": False,
                "error": "Low confidence in generated query",
                "confidence": result.get('confidence'),
                "suggestion": "Please rephrase your question or be more specific"
            }
        
        return result

# Usage
prod_gen = ProductionSQLGenerator(schema)

result = prod_gen.generate("What was our AWS spend last month?")
if result['success']:
    print(f"SQL: {result['sql']}")
    print(f"Confidence: {result['confidence']:.2%}")
```

**Week 4 Checklist:**
- [ ] Handle complex multi-step queries
- [ ] Implement conversational context
- [ ] Add confidence scoring
- [ ] Built production-ready SQL generator
- [ ] 90%+ accuracy on extended test suite

---

### Week 5: RAG Implementation - Part 1

**Goals:**
- Understand vector embeddings
- Set up ChromaDB
- Build knowledge base
- Implement retrieval

**Day 1-2: Vector Database Basics (6 hours)**

```python
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db"
))

# Create collection
collection = client.create_collection(
    name="finops_knowledge",
    metadata={"description": "FinOps chatbot knowledge base"}
)

# Add documents
documents = [
    "The aws_costs table contains daily cost data for all AWS services",
    "Teams are stored in the 'team' column and include Engineering, Marketing, Sales, and Data",
    "For last month queries, use: WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)",
    "EC2 costs are usually the largest component of AWS spending",
    "Production environment costs are typically 3-4x higher than development",
    "Reserved instances show as 'RI' in the pricing_model column",
    "Cost anomalies are defined as >20% deviation from 7-day average",
]

ids = [f"doc_{i}" for i in range(len(documents))]

collection.add(
    documents=documents,
    ids=ids
)

# Query for relevant context
results = collection.query(
    query_texts=["How do I query for last month?"],
    n_results=2
)

print("Relevant documents:")
for doc in results['documents'][0]:
    print(f"  - {doc}")
```

**Exercises:**
1. Add 50 pieces of knowledge about your FinOps domain
2. Include: schema info, common patterns, business rules, glossary
3. Test retrieval with 20 questions
4. Measure relevance of retrieved docs

**Knowledge Base Categories:**

```python
knowledge_base = {
    "schema": [
        "Table aws_costs has columns: date, team, service, cost, environment",
        "Table azure_costs has columns: date, subscription, resource_group, cost",
        # ... more schema info
    ],
    "sql_patterns": [
        "For monthly totals: SELECT SUM(cost) FROM table WHERE date >= DATE_TRUNC('month', CURRENT_DATE)",
        "For top N: Use ORDER BY cost DESC LIMIT N",
        # ... more patterns
    ],
    "business_rules": [
        "Production costs should be allocated to product teams",
        "Development costs are split 50/50 between Engineering and Data",
        # ... more rules
    ],
    "glossary": [
        "RI = Reserved Instance, a cost-saving pricing model",
        "Spot = Spot instance, cheapest but can be terminated",
        # ... more terms
    ],
    "examples": [
        "Q: Total EC2 cost | SQL: SELECT SUM(cost) FROM aws_costs WHERE service='EC2'",
        # ... more examples
    ]
}

# Add all to ChromaDB
for category, items in knowledge_base.items():
    for i, item in enumerate(items):
        collection.add(
            documents=[item],
            metadatas=[{"category": category}],
            ids=[f"{category}_{i}"]
        )
```

**Day 3-4: Embeddings & Retrieval (6 hours)**

```python
# Understanding embeddings
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create embeddings
texts = [
    "What was total cost?",
    "Show me spending breakdown",
    "How much did we spend?"
]

embeddings = model.encode(texts)
print(f"Embedding shape: {embeddings.shape}")  # (3, 384)

# Embeddings are numeric representations
print(f"First embedding: {embeddings[0][:10]}...")  # First 10 numbers

# Similar questions have similar embeddings
from sklearn.metrics.pairwise import cosine_similarity

similarity = cosine_similarity([embeddings[0]], [embeddings[2]])[0][0]
print(f"Similarity between Q1 and Q3: {similarity:.3f}")  # High similarity!
```

**Build Smart Retrieval:**

```python
class KnowledgeRetriever:
    def __init__(self, collection):
        self.collection = collection
    
    def retrieve_context(self, question, n_results=3):
        """Retrieve relevant context for a question"""
        
        # Query vector database
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        
        if not results['documents']:
            return []
        
        # Format context
        context = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            context.append({
                "text": doc,
                "category": metadata.get('category', 'unknown'),
                "distance": results['distances'][0][i] if results['distances'] else None
            })
        
        return context
    
    def format_context_for_prompt(self, context):
        """Format retrieved context for LLM prompt"""
        if not context:
            return "No relevant context found."
        
        formatted = "Relevant Context:\n\n"
        for item in context:
            formatted += f"- {item['text']}\n"
        
        return formatted

# Usage
retriever = KnowledgeRetriever(collection)

question = "How do I calculate last month's costs?"
context = retriever.retrieve_context(question)

print(retriever.format_context_for_prompt(context))
```

**Day 5-6: RAG Pipeline (8 hours)**

```python
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate

class RAGSQLGenerator:
    def __init__(self, schema, collection):
        self.schema = schema
        self.retriever = KnowledgeRetriever(collection)
        self.llm = Ollama(model="llama3.2")
        self.validator = QueryValidator()
    
    def generate_with_rag(self, question):
        """Generate SQL using RAG"""
        
        # Step 1: Retrieve relevant context
        context = self.retriever.retrieve_context(question, n_results=5)
        context_text = self.retriever.format_context_for_prompt(context)
        
        # Step 2: Create enhanced prompt
        prompt_template = """You are a SQL expert for a FinOps database.

{context}

Database Schema:
{schema}

Question: {question}

Generate a SQL query to answer this question. Use the context above for guidance.
Return ONLY the SQL query with no explanation.

SQL:"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "schema", "question"]
        )
        
        # Step 3: Generate SQL
        chain = prompt | self.llm
        
        schema_text = create_schema_prompt(self.schema)
        
        raw_sql = chain.invoke({
            "context": context_text,
            "schema": schema_text,
            "question": question
        })
        
        # Step 4: Validate and clean
        sql = self.validator.sanitize(raw_sql)
        validation = self.validator.validate(sql)
        
        if not validation['valid']:
            return {
                "success": False,
                "error": "Validation failed",
                "details": validation['errors']
            }
        
        return {
            "success": True,
            "sql": sql,
            "context_used": [c['text'] for c in context],
            "question": question
        }

# Test RAG vs Non-RAG
rag_gen = RAGSQLGenerator(schema, collection)
basic_gen = TextToSQLConverter(schema)

test_questions = [
    "What were our RI costs?",  # Uses glossary context
    "Show production spending trends",  # Uses business rules
    "Calculate monthly totals",  # Uses SQL patterns
]

for q in test_questions:
    print(f"\nQuestion: {q}")
    
    # With RAG
    rag_result = rag_gen.generate_with_rag(q)
    print(f"RAG SQL: {rag_result.get('sql', 'Failed')}")
    print(f"Context: {rag_result.get('context_used', [])[:2]}")
    
    # Without RAG
    basic_result = basic_gen.generate_sql(q)
    print(f"Basic SQL: {basic_result.get('sql', 'Failed')}")
```

**Day 7: RAG Optimization (6 hours)**

```python
# Optimize retrieval
class OptimizedRetriever:
    def __init__(self, collection):
        self.collection = collection
    
    def hybrid_search(self, question):
        """Combine semantic and keyword search"""
        
        # Semantic search (vector similarity)
        semantic_results = self.collection.query(
            query_texts=[question],
            n_results=10
        )
        
        # Keyword search (filter by metadata)
        keywords = self.extract_keywords(question)
        keyword_results = self.collection.query(
            query_texts=[question],
            n_results=10,
            where={"category": {"$in": keywords}}
        )
        
        # Merge and deduplicate
        all_results = self.merge_results(semantic_results, keyword_results)
        
        return all_results[:5]  # Top 5
    
    def extract_keywords(self, question):
        """Extract relevant categories from question"""
        category_keywords = {
            "schema": ["table", "column", "field"],
            "sql_patterns": ["how to", "query", "calculate"],
            "business_rules": ["should", "policy", "rule"],
            "glossary": ["what is", "define", "meaning"],
        }
        
        categories = []
        q_lower = question.lower()
        
        for category, keywords in category_keywords.items():
            if any(kw in q_lower for kw in keywords):
                categories.append(category)
        
        return categories if categories else list(category_keywords.keys())
    
    def merge_results(self, *result_sets):
        """Merge and deduplicate results"""
        seen = set()
        merged = []
        
        for results in result_sets:
            for doc in results['documents'][0]:
                if doc not in seen:
                    seen.add(doc)
                    merged.append(doc)
        
        return merged
```

**Week 5 Checklist:**
- [ ] Understand vector embeddings concept
- [ ] Set up ChromaDB
- [ ] Built knowledge base (50+ items)
- [ ] Implemented retrieval system
- [ ] Created RAG-powered SQL generator
- [ ] Measured improvement vs non-RAG

---

### Week 6: RAG Implementation - Part 2

**Goals:**
- Advanced RAG techniques
- Multi-turn conversations
- Context management
- Performance optimization

**Day 1-2: Conversation Memory (6 hours)**

```python
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory

class ConversationalRAG:
    def __init__(self, rag_generator):
        self.rag_gen = rag_generator
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.context = {
            "last_queries": [],
            "current_topic": None,
            "user_preferences": {}
        }
    
    def chat(self, question):
        """Handle conversational interaction"""
        
        # Check if question refers to previous context
        if self.refers_to_previous(question):
            question = self.resolve_reference(question)
        
        # Generate SQL with RAG
        result = self.rag_gen.generate_with_rag(question)
        
        # Update memory
        if result['success']:
            self.memory.save_context(
                {"input": question},
                {"output": result['sql']}
            )
            self.context['last_queries'].append({
                "question": question,
                "sql": result['sql']
            })
        
        return result
    
    def refers_to_previous(self, question):
        """Check if question refers to previous context"""
        references = [
            "that", "it", "same", "also", "too",
            "what about", "how about", "and"
        ]
        return any(ref in question.lower() for ref in references)
    
    def resolve_reference(self, question):
        """Resolve references to previous context"""
        if not self.context['last_queries']:
            return question
        
        last_q = self.context['last_queries'][-1]['question']
        
        prompt = f"""Previous question: {last_q}
        Current question: {question}
        
        Rewrite the current question as a complete, standalone question:"""
        
        llm = Ollama(model="llama3.2")
        resolved = llm.invoke(prompt)
        
        return resolved

# Example conversation
conv_rag = ConversationalRAG(rag_gen)

# Turn 1
result1 = conv_rag.chat("What was EC2 cost last month?")
print(f"Q1: {result1['sql']}\n")

# Turn 2 (refers to "EC2" from turn 1)
result2 = conv_rag.chat("What about S3?")
print(f"Q2: {result2['sql']}\n")

# Turn 3 (refers to "last month" from turn 1)
result3 = conv_rag.chat("Same for this month")
print(f"Q3: {result3['sql']}")
```

**Day 3-4: Query History & Learning (6 hours)**

```python
class LearningRAG:
    def __init__(self, rag_generator, collection):
        self.rag_gen = rag_generator
        self.collection = collection
        self.query_history = []
    
    def learn_from_feedback(self, question, sql, was_correct):
        """Learn from user feedback"""
        
        if was_correct:
            # Add to knowledge base as example
            self.collection.add(
                documents=[f"Q: {question} | SQL: {sql}"],
                metadatas=[{"category": "examples", "source": "user_feedback"}],
                ids=[f"user_example_{len(self.query_history)}"]
            )
        
        # Store in history
        self.query_history.append({
            "question": question,
            "sql": sql,
            "correct": was_correct,
            "timestamp": "2026-01-25"  # In production, use actual timestamp
        })
    
    def get_similar_queries(self, question):
        """Find similar questions from history"""
        
        results = self.collection.query(
            query_texts=[question],
            where={"category": "examples"},
            n_results=3
        )
        
        return results['documents'][0] if results['documents'] else []
    
    def generate_with_learning(self, question):
        """Generate SQL using learned examples"""
        
        # Find similar past queries
        similar = self.get_similar_queries(question)
        
        if similar:
            # Add to prompt
            examples_text = "\n".join([f"  {ex}" for ex in similar])
            enhanced_question = f"{question}\n\nSimilar past queries:\n{examples_text}"
        else:
            enhanced_question = question
        
        return self.rag_gen.generate_with_rag(enhanced_question)

# Usage with feedback loop
learning_rag = LearningRAG(rag_gen, collection)

# User asks question
result = learning_rag.generate_with_learning("Show me RDS costs")
print(f"Generated: {result['sql']}")

# User provides feedback
learning_rag.learn_from_feedback(
    question="Show me RDS costs",
    sql=result['sql'],
    was_correct=True
)

# Next similar question will benefit from this example
result2 = learning_rag.generate_with_learning("Show me Lambda costs")
print(f"Generated (with learning): {result2['sql']}")
```

**Day 5-6: Performance & Caching (6 hours)**

```python
import hashlib
import json
from functools import lru_cache

class CachedRAG:
    def __init__(self, rag_generator):
        self.rag_gen = rag_generator
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def generate_cache_key(self, question):
        """Generate cache key from question"""
        # Normalize question
        normalized = question.lower().strip()
        # Create hash
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def generate_cached(self, question):
        """Generate SQL with caching"""
        
        cache_key = self.generate_cache_key(question)
        
        # Check cache
        if cache_key in self.cache:
            self.cache_hits += 1
            return {
                **self.cache[cache_key],
                "from_cache": True
            }
        
        # Generate fresh
        self.cache_misses += 1
        result = self.rag_gen.generate_with_rag(question)
        
        # Store in cache
        if result['success']:
            self.cache[cache_key] = result
        
        return {
            **result,
            "from_cache": False
        }
    
    def get_stats(self):
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.1%}"
        }

# Test caching
cached_rag = CachedRAG(rag_gen)

# First query - cache miss
result1 = cached_rag.generate_cached("Total EC2 costs")
print(f"From cache: {result1['from_cache']}")

# Same query - cache hit
result2 = cached_rag.generate_cached("Total EC2 costs")
print(f"From cache: {result2['from_cache']}")

# Slightly different wording - cache hit (due to normalization)
result3 = cached_rag.generate_cached("total ec2 costs")
print(f"From cache: {result3['from_cache']}")

print(f"\nStats: {cached_rag.get_stats()}")
```

**Batch Processing:**

```python
class BatchRAG:
    def __init__(self, rag_generator):
        self.rag_gen = rag_generator
    
    def generate_batch(self, questions):
        """Process multiple questions efficiently"""
        
        results = []
        
        # Batch retrieve context (more efficient)
        all_contexts = self.rag_gen.retriever.collection.query(
            query_texts=questions,
            n_results=5
        )
        
        # Process each question
        for i, question in enumerate(questions):
            # Use pre-retrieved context
            context = [
                {"text": doc} for doc in all_contexts['documents'][i]
            ]
            
            # Generate SQL
            # ... implementation
            
            results.append({
                "question": question,
                "sql": "...",  # Generated SQL
                "context": context
            })
        
        return results

# Usage
batch_rag = BatchRAG(rag_gen)

questions = [
    "Total costs by team",
    "EC2 costs last month",
    "Top 5 services by cost"
]

results = batch_rag.generate_batch(questions)
for r in results:
    print(f"{r['question']}: {r['sql']}")
```

**Day 7: Integration & Testing (6 hours)**

Combine all RAG features:

```python
class ProductionRAG:
    def __init__(self, schema, collection):
        # Core components
        self.rag_gen = RAGSQLGenerator(schema, collection)
        
        # Advanced features
        self.conv_rag = ConversationalRAG(self.rag_gen)
        self.learning_rag = LearningRAG(self.rag_gen, collection)
        self.cached_rag = CachedRAG(self.rag_gen)
        
        # Stats
        self.query_count = 0
    
    def ask(self, question, use_cache=True, context=None):
        """Main entry point"""
        
        self.query_count += 1
        
        # Use appropriate generator
        if use_cache:
            result = self.cached_rag.generate_cached(question)
        elif context:
            result = self.conv_rag.chat(question)
        else:
            result = self.learning_rag.generate_with_learning(question)
        
        return result
    
    def provide_feedback(self, question, sql, was_correct):
        """User feedback for learning"""
        self.learning_rag.learn_from_feedback(question, sql, was_correct)
    
    def get_statistics(self):
        """Get system stats"""
        return {
            "total_queries": self.query_count,
            "cache_stats": self.cached_rag.get_stats(),
            "knowledge_base_size": self.learning_rag.collection.count()
        }

# Production usage
prod_rag = ProductionRAG(schema, collection)

# Query with caching
result = prod_rag.ask("What was EC2 cost?", use_cache=True)

# Provide feedback
prod_rag.provide_feedback("What was EC2 cost?", result['sql'], was_correct=True)

# Get stats
stats = prod_rag.get_statistics()
print(f"Stats: {json.dumps(stats, indent=2)}")
```

**Week 6 Checklist:**
- [ ] Implemented conversation memory
- [ ] Built learning system from feedback
- [ ] Added caching for performance
- [ ] Created production-ready RAG system
- [ ] Tested with realistic conversation flows

---

### Week 7: Backend Development

**Goals:**
- Build FastAPI backend
- Database integration
- API endpoints
- Error handling

**Day 1-2: FastAPI Basics (6 hours)**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Define request/response models
class QueryRequest(BaseModel):
    question: str
    use_cache: bool = True
    context: dict = None

class QueryResponse(BaseModel):
    success: bool
    sql: str = None
    error: str = None
    confidence: float = None
    context_used: list = []

# Create app
app = FastAPI(
    title="FinOps Chatbot API",
    description="SQL generation from natural language",
    version="1.0.0"
)

# Initialize RAG system (global)
# In production, use dependency injection
prod_rag = None  # Will be initialized on startup

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global prod_rag
    # Load schema and collection
    prod_rag = ProductionRAG(schema, collection)
    print("RAG system initialized")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "FinOps Chatbot"}

@app.post("/query", response_model=QueryResponse)
async def generate_query(request: QueryRequest):
    """Generate SQL from natural language"""
    try:
        result = prod_rag.ask(
            request.question,
            use_cache=request.use_cache,
            context=request.context
        )
        
        return QueryResponse(
            success=result['success'],
            sql=result.get('sql'),
            error=result.get('error'),
            confidence=result.get('confidence'),
            context_used=result.get('context_used', [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def provide_feedback(
    question: str,
    sql: str,
    was_correct: bool
):
    """Record user feedback"""
    try:
        prod_rag.provide_feedback(question, sql, was_correct)
        return {"status": "feedback recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return prod_rag.get_statistics()

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Test the API:**

```bash
# Terminal 1: Start server
python api.py

# Terminal 2: Test endpoints
curl http://localhost:8000/

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What was EC2 cost last month?"}'

curl http://localhost:8000/stats
```

**Day 3-4: Database Integration (6 hours)**

```python
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

class DatabaseExecutor:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.timeout_seconds = 30
    
    def execute_query(self, sql):
        """Execute SQL and return results"""
        try:
            # Connect to database
            conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor,
                connect_timeout=10
            )
            
            # Set query timeout
            cursor = conn.cursor()
            cursor.execute(f"SET statement_timeout = {self.timeout_seconds * 1000}")
            
            # Execute query
            cursor.execute(sql)
            
            # Fetch results
            results = cursor.fetchall()
            
            # Convert to list of dicts
            data = [dict(row) for row in results]
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "data": data,
                "row_count": len(data)
            }
        
        except psycopg2.Error as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "database_error"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "unknown_error"
            }

# Add to API
db_executor = DatabaseExecutor("postgresql://user:pass@localhost/finops")

@app.post("/execute")
async def execute_query_endpoint(request: QueryRequest):
    """Generate SQL and execute it"""
    
    # Generate SQL
    sql_result = prod_rag.ask(request.question)
    
    if not sql_result['success']:
        return {
            "success": False,
            "error": sql_result.get('error')
        }
    
    # Execute query
    exec_result = db_executor.execute_query(sql_result['sql'])
    
    return {
        "success": exec_result['success'],
        "sql": sql_result['sql'],
        "data": exec_result.get('data'),
        "row_count": exec_result.get('row_count'),
        "error": exec_result.get('error')
    }
```

**Day 5-6: Advanced API Features (8 hours)**

```python
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json

# Async query generation
@app.post("/query/async")
async def generate_query_async(
    request: QueryRequest,
    background_tasks: BackgroundTasks
):
    """Generate SQL asynchronously"""
    
    task_id = str(uuid.uuid4())
    
    # Start background task
    background_tasks.add_task(
        process_query,
        task_id,
        request.question
    )
    
    return {
        "task_id": task_id,
        "status": "processing"
    }

@app.get("/query/status/{task_id}")
async def get_query_status(task_id: str):
    """Check status of async query"""
    # Implementation depends on your task storage
    pass

# Streaming responses for long queries
@app.post("/query/stream")
async def stream_query(request: QueryRequest):
    """Stream query generation process"""
    
    async def generate():
        # Yield progress updates
        yield json.dumps({"status": "retrieving_context"}) + "\n"
        
        # Retrieve context
        context = prod_rag.rag_gen.retriever.retrieve_context(request.question)
        yield json.dumps({"status": "context_retrieved", "count": len(context)}) + "\n"
        
        # Generate SQL
        yield json.dumps({"status": "generating_sql"}) + "\n"
        result = prod_rag.ask(request.question)
        
        # Yield final result
        yield json.dumps({"status": "complete", "result": result}) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")

# Batch endpoint
@app.post("/query/batch")
async def batch_query(questions: list[str]):
    """Process multiple questions"""
    
    results = []
    for question in questions:
        result = prod_rag.ask(question)
        results.append({
            "question": question,
            "result": result
        })
    
    return {"results": results}

# Authentication (basic example)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API token"""
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

@app.post("/query/secure")
async def secure_query(
    request: QueryRequest,
    token: str = Security(verify_token)
):
    """Authenticated endpoint"""
    return await generate_query(request)
```

**Day 7: Testing & Documentation (6 hours)**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_query_endpoint():
    response = client.post(
        "/query",
        json={"question": "Total costs"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    assert "SELECT" in result["sql"].upper()

def test_invalid_query():
    response = client.post(
        "/query",
        json={"question": "DROP TABLE users"}
    )
    result = response.json()
    assert result["success"] == False

def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    assert "total_queries" in response.json()

# Run tests
# pytest tests/test_api.py -v
```

**API Documentation (auto-generated by FastAPI):**

```python
# Add to app
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="FinOps Chatbot API",
        version="1.0.0",
        description="Generate SQL queries from natural language questions about FinOps data",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Access docs at: http://localhost:8000/docs
```

**Week 7 Checklist:**
- [ ] Built FastAPI backend
- [ ] Integrated database execution
- [ ] Created all API endpoints
- [ ] Added authentication
- [ ] Wrote tests
- [ ] Generated API documentation

---

### Week 8: Frontend Development

**Goals:**
- Build Streamlit UI
- Create chat interface
- Add visualizations
- User experience

**Day 1-2: Streamlit Basics (6 hours)**

```python
# app.py
import streamlit as st
import requests
import pandas as pd

# Configuration
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="FinOps Chatbot",
    page_icon="💰",
    layout="wide"
)

# Title
st.title("💰 FinOps Chatbot")
st.markdown("Ask questions about your cloud costs in natural language")

# Sidebar
with st.sidebar:
    st.header("Settings")
    use_cache = st.checkbox("Use cache", value=True)
    show_sql = st.checkbox("Show SQL query", value=True)
    
    st.markdown("---")
    st.markdown("### Examples")
    st.markdown("""
    - What was EC2 cost last month?
    - Show top 5 teams by spending
    - Compare prod vs dev costs
    """)

# Main chat interface
question = st.text_input(
    "Ask a question:",
    placeholder="e.g., What was our total AWS spend last month?"
)

if st.button("Ask") or question:
    if question:
        # Call API
        with st.spinner("Generating query..."):
            response = requests.post(
                f"{API_URL}/query",
                json={
                    "question": question,
                    "use_cache": use_cache
                }
            )
        
        if response.status_code == 200:
            result = response.json()
            
            if result["success"]:
                # Show SQL
                if show_sql:
                    st.code(result["sql"], language="sql")
                
                # Execute and show results
                with st.spinner("Executing query..."):
                    exec_response = requests.post(
                        f"{API_URL}/execute",
                        json={"question": question}
                    )
                
                if exec_response.status_code == 200:
                    exec_result = exec_response.json()
                    
                    if exec_result["success"]:
                        # Display data
                        df = pd.DataFrame(exec_result["data"])
                        st.dataframe(df)
                        
                        # Show row count
                        st.success(f"Found {exec_result['row_count']} rows")
                    else:
                        st.error(f"Error: {exec_result['error']}")
            else:
                st.error(f"Error: {result['error']}")
        else:
            st.error("API request failed")

# Run: streamlit run app.py
```

**Day 3-4: Enhanced Chat Interface (8 hours)**

```python
import streamlit as st
from datetime import datetime

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = {}

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if "sql" in message:
            with st.expander("View SQL"):
                st.code(message["sql"], language="sql")
        
        if "data" in message and message["data"]:
            df = pd.DataFrame(message["data"])
            st.dataframe(df, use_container_width=True)

# Chat input
if prompt := st.chat_input("Ask about your costs..."):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now()
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Call API with context
            response = requests.post(
                f"{API_URL}/query",
                json={
                    "question": prompt,
                    "use_cache": True,
                    "context": st.session_state.conversation_context
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result["success"]:
                    # Show SQL
                    with st.expander("View SQL", expanded=False):
                        st.code(result["sql"], language="sql")
                    
                    # Execute query
                    exec_response = requests.post(
                        f"{API_URL}/execute",
                        json={"question": prompt}
                    )
                    
                    if exec_response.status_code == 200:
                        exec_result = exec_response.json()
                        
                        if exec_result["success"]:
                            df = pd.DataFrame(exec_result["data"])
                            
                            # Smart formatting based on data
                            if len(df) == 1 and len(df.columns) == 1:
                                # Single value - show as metric
                                value = df.iloc[0, 0]
                                st.metric(
                                    label="Result",
                                    value=f"${value:,.2f}" if isinstance(value, (int, float)) else value
                                )
                            else:
                                # Table - show as dataframe
                                st.dataframe(df, use_container_width=True)
                                
                                # Auto-visualization if numeric
                                numeric_cols = df.select_dtypes(include=['number']).columns
                                if len(numeric_cols) > 0 and len(df) > 1:
                                    st.bar_chart(df.set_index(df.columns[0])[numeric_cols[0]])
                            
                            # Add to message history
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"Found {len(df)} results",
                                "sql": result["sql"],
                                "data": exec_result["data"],
                                "timestamp": datetime.now()
                            })
                            
                            # Update context
                            st.session_state.conversation_context = {
                                "last_query": result["sql"],
                                "last_question": prompt
                            }
                        else:
                            st.error(exec_result["error"])
                else:
                    st.error(result["error"])

# Sidebar - conversation controls
with st.sidebar:
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.conversation_context = {}
        st.rerun()
    
    if st.session_state.messages:
        st.markdown("### Conversation History")
        st.markdown(f"{len(st.session_state.messages)} messages")
```

**Day 5-6: Visualizations & Analytics (8 hours)**

```python
import plotly.express as px
import plotly.graph_objects as go

def create_visualization(df, question):
    """Auto-generate appropriate visualization"""
    
    # Detect chart type based on data
    if len(df.columns) == 2:
        col1, col2 = df.columns
        
        # Time series
        if pd.api.types.is_datetime64_any_dtype(df[col1]):
            fig = px.line(
                df,
                x=col1,
                y=col2,
                title=f"{col2} over time"
            )
        
        # Categorical vs numeric
        elif pd.api.types.is_numeric_dtype(df[col2]):
            # Bar chart
            fig = px.bar(
                df,
                x=col1,
                y=col2,
                title=question
            )
            
            # Add pie chart option
            if len(df) <= 10:
                st.plotly_chart(
                    px.pie(df, values=col2, names=col1),
                    use_container_width=True
                )
        else:
            fig = None
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Multi-column heatmap
    elif len(df.columns) > 2 and all(pd.api.types.is_numeric_dtype(df[col]) for col in df.columns[1:]):
        fig = px.imshow(
            df.set_index(df.columns[0]),
            title=question,
            color_continuous_scale="RdYlGn_r"
        )
        st.plotly_chart(fig, use_container_width=True)

# Add to chat interface
if exec_result["success"]:
    df = pd.DataFrame(exec_result["data"])
    
    # Show data
    st.dataframe(df)
    
    # Auto-visualize
    create_visualization(df, prompt)

# Dashboard view
st.markdown("---")
st.header("Quick Insights")

col1, col2, col3 = st.columns(3)

with col1:
    # Total spend metric
    total_response = requests.post(
        f"{API_URL}/execute",
        json={"question": "What is total cost this month?"}
    )
    if total_response.status_code == 200:
        result = total_response.json()
        if result["success"] and result["data"]:
            total = result["data"][0].get("total", 0)
            st.metric("This Month", f"${total:,.0f}")

with col2:
    # Top service
    service_response = requests.post(
        f"{API_URL}/execute",
        json={"question": "What is the most expensive service?"}
    )
    if service_response.status_code == 200:
        result = service_response.json()
        if result["success"] and result["data"]:
            service = result["data"][0].get("service", "N/A")
            st.metric("Top Service", service)

with col3:
    # Trend
    st.metric("Trend", "↗ 12%", delta="vs last month")
```

**Day 7: Polish & UX (6 hours)**

```python
# Add loading states
with st.spinner("🔍 Analyzing your question..."):
    time.sleep(0.5)  # Visual feedback

# Add helpful error messages
if not result["success"]:
    error = result["error"]
    
    # Provide suggestions
    if "validation" in error.lower():
        st.error("⚠️ Query validation failed")
        st.info("💡 Try rephrasing your question or asking for something simpler")
    elif "timeout" in error.lower():
        st.error("⏱️ Query took too long")
        st.info("💡 Try being more specific or asking about a shorter time period")
    else:
        st.error(f"❌ Error: {error}")

# Add examples as buttons
st.markdown("### Try these examples:")
examples = [
    "What was total cost last month?",
    "Show top 5 teams by spending",
    "Compare EC2 vs S3 costs"
]

cols = st.columns(len(examples))
for i, example in enumerate(examples):
    if cols[i].button(example, key=f"example_{i}"):
        st.session_state.example_question = example
        st.rerun()

# Export functionality
if st.session_state.messages:
    # Export conversation
    if st.button("📥 Export conversation"):
        export_data = {
            "messages": st.session_state.messages,
            "timestamp": datetime.now().isoformat()
        }
        
        st.download_button(
            "Download JSON",
            data=json.dumps(export_data, indent=2, default=str),
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Feedback mechanism
if st.session_state.messages:
    last_msg = st.session_state.messages[-1]
    
    if last_msg["role"] == "assistant":
        st.markdown("### Was this helpful?")
        col1, col2 = st.columns(2)
        
        if col1.button("👍 Yes"):
            requests.post(
                f"{API_URL}/feedback",
                params={
                    "question": last_msg.get("question", ""),
                    "sql": last_msg.get("sql", ""),
                    "was_correct": True
                }
            )
            st.success("Thanks for your feedback!")
        
        if col2.button("👎 No"):
            feedback = st.text_input("What went wrong?")
            if feedback:
                # Store feedback
                st.info("Feedback recorded")
```

**Week 8 Checklist:**
- [ ] Built Streamlit chat interface
- [ ] Added conversation history
- [ ] Created auto-visualizations
- [ ] Implemented dashboard
- [ ] Added export and feedback
- [ ] Polished UX

---

### Week 9-10: Production Ready

**Goals:**
- Error handling & logging
- Security & validation
- Deployment
- Documentation

**Week 9: Day 1-3 - Error Handling & Logging**

```python
import logging
from logging.handlers import RotatingFileHandler
import traceback

# Configure logging
def setup_logging():
    # Create logger
    logger = logging.getLogger("finops_chatbot")
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        'logs/chatbot.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# Error handling in API
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    
    # Log error
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host
        }
    )
    
    # Return error response
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if app.debug else "An error occurred",
            "type": type(exc).__name__
        }
    )

# Structured logging
class RequestLogger:
    def __init__(self):
        self.logger = logging.getLogger("requests")
    
    def log_request(self, question, result, duration):
        """Log request details"""
        self.logger.info(
            "Query processed",
            extra={
                "question": question,
                "success": result.get("success"),
                "duration_ms": duration * 1000,
                "sql_length": len(result.get("sql", "")),
                "from_cache": result.get("from_cache", False)
            }
        )

# Monitoring
from prometheus_client import Counter, Histogram, generate_latest

query_counter = Counter('queries_total', 'Total queries processed')
query_duration = Histogram('query_duration_seconds', 'Query processing time')
error_counter = Counter('errors_total', 'Total errors', ['error_type'])

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")
```

**Week 9: Day 4-5 - Security**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Security configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User authentication
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return username

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/query")
@limiter.limit("10/minute")
async def generate_query_limited(
    request: Request,
    query_request: QueryRequest,
    current_user: str = Depends(get_current_user)
):
    """Rate-limited query endpoint"""
    # Implementation
    pass

# Input validation
from pydantic import validator

class QueryRequest(BaseModel):
    question: str
    use_cache: bool = True
    
    @validator('question')
    def validate_question(cls, v):
        if len(v) < 3:
            raise ValueError('Question too short')
        if len(v) > 500:
            raise ValueError('Question too long')
        
        # Check for SQL injection attempts
        dangerous = ['DROP', 'DELETE', 'UPDATE', '--', ';']
        if any(d in v.upper() for d in dangerous):
            raise ValueError('Invalid question')
        
        return v
```

**Week 9: Day 6-7 - Testing**

```python
# tests/integration_test.py
import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

class TestIntegration:
    def test_full_workflow(self):
        """Test complete user workflow"""
        
        # 1. Ask question
        response = client.post(
            "/query",
            json={"question": "Total costs last month"}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        sql = result["sql"]
        
        # 2. Execute query
        exec_response = client.post(
            "/execute",
            json={"question": "Total costs last month"}
        )
        assert exec_response.status_code == 200
        exec_result = exec_response.json()
        assert exec_result["success"] == True
        
        # 3. Provide feedback
        feedback_response = client.post(
            "/feedback",
            params={
                "question": "Total costs last month",
                "sql": sql,
                "was_correct": True
            }
        )
        assert feedback_response.status_code == 200
    
    def test_conversation_context(self):
        """Test multi-turn conversation"""
        
        # First question
        response1 = client.post(
            "/query",
            json={"question": "EC2 costs"}
        )
        result1 = response1.json()
        
        # Follow-up using context
        response2 = client.post(
            "/query",
            json={
                "question": "What about S3?",
                "context": {
                    "last_question": "EC2 costs",
                    "last_query": result1["sql"]
                }
            }
        )
        result2 = response2.json()
        
        assert "S3" in result2["sql"]
    
    def test_error_handling(self):
        """Test error scenarios"""
        
        # Invalid question
        response = client.post(
            "/query",
            json={"question": "x"}
        )
        assert response.status_code == 422  # Validation error
        
        # Malicious question
        response = client.post(
            "/query",
            json={"question": "DROP TABLE users"}
        )
        result = response.json()
        assert result["success"] == False

# Performance testing
def test_performance():
    """Test response times"""
    import time
    
    start = time.time()
    response = client.post(
        "/query",
        json={"question": "Total costs"}
    )
    duration = time.time() - start
    
    assert duration < 2.0  # Should respond in < 2 seconds
    assert response.status_code == 200

# Load testing with locust
from locust import HttpUser, task, between

class ChatbotUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def ask_question(self):
        self.client.post(
            "/query",
            json={"question": "Total costs"}
        )

# Run: locust -f tests/load_test.py
```

**Week 10: Deployment**

```python
# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/finops
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - chromadb
    volumes:
      - ./logs:/app/logs
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=finops
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
  
  streamlit:
    build:
      context: .
      dockerfile: docker/Dockerfile.streamlit
    ports:
      - "8501:8501"
    depends_on:
      - api

volumes:
  postgres_data:
  chroma_data:
```

**Kubernetes Deployment:**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finops-chatbot-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: finops-chatbot-api
  template:
    metadata:
      labels:
        app: finops-chatbot-api
    spec:
      containers:
      - name: api
        image: finops-chatbot:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: finops-chatbot-service
spec:
  selector:
    app: finops-chatbot-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Week 10: Documentation**

```markdown
# FinOps Chatbot Documentation

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Docker (optional)

### Installation

1. Clone repository:
\`\`\`bash
git clone https://github.com/yourorg/finops-chatbot
cd finops-chatbot
\`\`\`

2. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. Set up environment:
\`\`\`bash
cp .env.example .env
# Edit .env with your configuration
\`\`\`

4. Initialize database:
\`\`\`bash
python scripts/init_db.py
\`\`\`

5. Run application:
\`\`\`bash
# API
uvicorn api:app --reload

# UI
streamlit run app.py
\`\`\`

## Architecture

[Include architecture diagram]

## API Reference

### POST /query
Generate SQL from natural language

**Request:**
\`\`\`json
{
  "question": "What was EC2 cost last month?",
  "use_cache": true
}
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "sql": "SELECT SUM(cost) FROM aws_costs...",
  "confidence": 0.95
}
\`\`\`

## Deployment

### Docker
\`\`\`bash
docker-compose up
\`\`\`

### Kubernetes
\`\`\`bash
kubectl apply -f k8s/
\`\`\`

## Troubleshooting

### Common Issues

**Issue:** Query validation fails
**Solution:** Check that question doesn't contain SQL keywords

**Issue:** Slow responses
**Solution:** Enable caching, optimize database queries

## Contributing

See CONTRIBUTING.md

## License

MIT License
```

**Week 9-10 Checklist:**
- [ ] Implemented comprehensive logging
- [ ] Added security (auth, rate limiting)
- [ ] Wrote integration tests
- [ ] Created Docker containers
- [ ] Set up Kubernetes deployment
- [ ] Wrote documentation
- [ ] Conducted load testing
- [ ] Prepared for production

---

## Resource Library

### Books
- **Python:**
  - "Python Crash Course" by Eric Matthes
  - "Fluent Python" by Luciano Ramalho

- **Machine Learning:**
  - "Hands-On Machine Learning" by Aurélien Géron
  - "Natural Language Processing with Transformers" by Lewis Tunstall

- **APIs:**
  - "Designing Data-Intensive Applications" by Martin Kleppmann

### Online Courses
- **LangChain:** Deeplearning.AI LangChain course
- **FastAPI:** Official FastAPI tutorial
- **Streamlit:** Streamlit documentation

### Documentation
- LangChain: https://python.langchain.com/
- Ollama: https://ollama.com/
- ChromaDB: https://docs.trychroma.com/
- FastAPI: https://fastapi.tiangolo.com/
- Streamlit: https://docs.streamlit.io/

### Communities
- LangChain Discord
- r/LocalLLaMA (Reddit)
- r/MachineLearning (Reddit)
- Stack Overflow

---

## Practice Projects

### Week 1-2 Practice
1. Build a simple chatbot CLI
2. Create a prompt engineering playground
3. Make a "prompt tester" that compares different prompts

### Week 3-4 Practice
1. Text-to-SQL for different domains (e-commerce, HR, etc.)
2. SQL validator library
3. Query complexity analyzer

### Week 5-6 Practice
1. Personal knowledge base (notes, bookmarks)
2. Document Q&A system
3. Code documentation assistant

### Week 7-8 Practice
1. Simple CRUD API
2. Real-time dashboard
3. Chat interface with memory

---

## Troubleshooting Guide

### Common Issues

**Problem:** "Module not found" errors
**Solution:**
\`\`\`bash
pip install --upgrade pip
pip install -r requirements.txt
\`\`\`

**Problem:** Ollama model not responding
**Solution:**
\`\`\`bash
# Check if Ollama is running
ollama list

# Restart Ollama
sudo systemctl restart ollama

# Re-pull model
ollama pull llama3.2
\`\`\`

**Problem:** ChromaDB connection errors
**Solution:**
\`\`\`python
# Reinitialize database
import chromadb
client = chromadb.Client()
client.reset()  # Warning: deletes all data
\`\`\`

**Problem:** Poor SQL generation quality
**Solutions:**
- Add more examples to knowledge base
- Improve schema documentation
- Use better prompts
- Try different model (CodeLlama)
- Increase context retrieval (n_results)

**Problem:** Slow performance
**Solutions:**
- Enable caching
- Use smaller models
- Reduce n_results in RAG
- Optimize database queries
- Add query timeouts

---

## Progress Tracking

### Week 1
- [ ] Environment setup complete
- [ ] First LLM interaction
- [ ] Basic Python refresher
- [ ] Simple chatbot prototype

### Week 2
- [ ] Prompt engineering skills
- [ ] LangChain basics
- [ ] Few-shot learning
- [ ] SQL generator v1

### Week 3
- [ ] Schema documentation
- [ ] Query validator
- [ ] Text-to-SQL system
- [ ] 80% accuracy achieved

### Week 4
- [ ] Complex query handling
- [ ] Conversation context
- [ ] Confidence scoring
- [ ] 90% accuracy achieved

### Week 5
- [ ] ChromaDB setup
- [ ] Knowledge base built
- [ ] Basic RAG pipeline
- [ ] Context retrieval working

### Week 6
- [ ] Conversation memory
- [ ] Learning from feedback
- [ ] Performance optimization
- [ ] Production RAG complete

### Week 7
- [ ] FastAPI backend
- [ ] Database integration
- [ ] All endpoints working
- [ ] API tests passing

### Week 8
- [ ] Streamlit UI
- [ ] Chat interface
- [ ] Visualizations
- [ ] Complete MVP

### Week 9
- [ ] Logging implemented
- [ ] Security added
- [ ] Integration tests
- [ ] Load testing done

### Week 10
- [ ] Docker containers
- [ ] Kubernetes deployment
- [ ] Documentation complete
- [ ] Production ready!

---

## Success Metrics

Track your progress:

**Knowledge:**
- [ ] Can explain RAG concept
- [ ] Can write effective prompts
- [ ] Understand vector embeddings
- [ ] Know FastAPI basics
- [ ] Comfortable with LangChain

**Skills:**
- [ ] Built working SQL generator (80%+ accuracy)
- [ ] Created RAG pipeline
- [ ] Developed API backend
- [ ] Built chat interface
- [ ] Deployed to production

**Project:**
- [ ] MVP working end-to-end
- [ ] 3+ users testing
- [ ] Positive feedback received
- [ ] Documentation complete
- [ ] Ready for stakeholder demo

---

## Next Steps After Completion

1. **Present to stakeholders**
   - Demo the system
   - Show ROI calculation
   - Get approval for rollout

2. **Expand to more data sources**
   - Azure costs
   - GCP costs
   - Custom databases

3. **Advanced features**
   - Proactive insights
   - Anomaly detection
   - Automated reports

4. **Scale the system**
   - More users
   - More data
   - Better performance

5. **Learn advanced topics**
   - Fine-tuning models
   - Advanced RAG techniques
   - Multi-agent systems

---

*You can do this! Start with Week 1, and take it one day at a time.*

**Remember:** Everyone who knows this stuff was once where you are now. The only difference is they started learning.

*Good luck! 🚀*