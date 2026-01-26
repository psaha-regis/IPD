# JSON Output Reference

## Overview

This document describes the structure and contents of the JSON files produced by `episodic_ipd_game.py`. Each experiment generates a single JSON file containing complete information about the game configuration, agent behavior, and outcomes.

**File naming convention**: `episodic_game_YYYYMMDD_HHMMSS.json`

---

## Top-Level Structure

```json
{
  "timestamp": "ISO 8601 datetime",
  "hostname": "string",
  "username": "string",
  "host_0": "string",
  "host_1": "string",
  "prompts": { ... },
  "config": { ... },
  "elapsed_seconds": float,
  "agent_0": { ... },
  "agent_1": { ... },
  "episodes": [ ... ]
}
```

---

## Field Reference

### Metadata Fields

#### `timestamp`
- **Type**: String (ISO 8601 format)
- **Example**: `"2025-01-26T14:30:45.123456"`
- **Description**: The date and time when the experiment completed
- **Usage**: For tracking when experiments were run, sorting results chronologically

#### `hostname`
- **Type**: String
- **Example**: `"platinum"`
- **Description**: The machine hostname where the experiment was executed (the orchestrator)
- **Usage**: Track which machine coordinated the experiment

#### `username`
- **Type**: String
- **Example**: `"dhart"`
- **Description**: The system username of the person who submitted the job
- **Usage**: Track who ran each experiment, useful for multi-user environments

#### `host_0`
- **Type**: String
- **Example**: `"iron"`, `"nickel"`, `"100.116.129.84"`
- **Description**: The hostname or IP address where Agent 0's LLM was running
- **Usage**: Track cluster resource utilization, identify which models ran where

#### `host_1`
- **Type**: String
- **Example**: `"iron"`, `"zinc"`
- **Description**: The hostname or IP address where Agent 1's LLM was running
- **Usage**: Track cluster resource utilization, identify which models ran where

---

### Prompts Section

#### `prompts`
- **Type**: Object
- **Description**: Contains the actual text of prompts used in the experiment

```json
"prompts": {
  "system_prompt": "You are participating in...",
  "reflection_template": "Reflect on your performance..."
}
```

##### `prompts.system_prompt`
- **Type**: String
- **Description**: The complete system prompt given to both agents at initialization
- **Length**: Typically 500-2000 characters
- **Usage**: Essential for reproducibility; documents the agent's initial framing and instructions
- **Note**: This is the actual text loaded from `system_prompt.txt` or the default prompt

##### `prompts.reflection_template`
- **Type**: String
- **Description**: The template used for post-episode reflections (if custom template was used)
- **Usage**: Documents any custom reflection prompting used in the experiment
- **Note**: Empty string if using built-in reflection templates

---

### Configuration Section

#### `config`
- **Type**: Object
- **Description**: Complete experimental configuration parameters

```json
"config": {
  "num_episodes": 5,
  "rounds_per_episode": 20,
  "total_rounds": 100,
  "history_window_size": 10,
  "temperature": 0.7,
  "reset_between_episodes": true,
  "reflection_type": "standard",
  "model_0": "llama3:8b-instruct-q5_K_M",
  "model_1": "llama3:8b-instruct-q5_K_M",
  "decision_token_limit": 256,
  "reflection_token_limit": 1024,
  "http_timeout": 60,
  "force_decision_retries": 2
}
```

##### `config.num_episodes`
- **Type**: Integer
- **Range**: 1-100+ (typically 5-10)
- **Description**: Number of distinct episodes (periods) in the game
- **Game Theory**: Episodes provide opportunities for strategic learning between periods

##### `config.rounds_per_episode`
- **Type**: Integer
- **Range**: 10-100+ (typically 10-50)
- **Description**: Number of IPD rounds played within each episode
- **Total Interactions**: `num_episodes × rounds_per_episode`

##### `config.total_rounds`
- **Type**: Integer
- **Calculation**: `num_episodes × rounds_per_episode`
- **Description**: Total number of IPD decisions made by each agent across all episodes
- **Usage**: Useful for normalizing cooperation rates and comparing experiments of different lengths

##### `config.history_window_size`
- **Type**: Integer
- **Range**: 3-50 (typically 5-20)
- **Description**: Number of recent rounds shown to agents in decision prompts
- **Example**: If set to 10, agents see the last 10 rounds when making decisions
- **Research Note**: Affects agent memory/context, may influence strategy learning

##### `config.temperature`
- **Type**: Float
- **Range**: 0.0-2.0 (typically 0.5-1.0)
- **Description**: LLM sampling temperature
- **Effect**: 
  - Lower (0.1-0.5): More deterministic, consistent responses
  - Medium (0.6-0.8): Balanced exploration/exploitation
  - Higher (0.9-1.5): More random, exploratory behavior

##### `config.reset_between_episodes`
- **Type**: Boolean
- **Description**: Whether conversation history is cleared between episodes
- **true**: Only system prompt + previous reflection kept; tactical history cleared
- **false**: Full conversation history maintained across all episodes
- **Research Impact**: Tests episodic vs. continuous memory on cooperation

##### `config.reflection_type`
- **Type**: String
- **Values**: `"minimal"`, `"standard"`, `"detailed"`
- **Description**: Depth of post-episode reflection prompting
- **minimal**: Brief strategic summary
- **standard**: Moderate analysis with strategy identification
- **detailed**: Deep analysis including counterfactuals and opponent modeling

##### `config.model_0` and `config.model_1`
- **Type**: String
- **Examples**: 
  - `"llama3:8b-instruct-q5_K_M"`
  - `"mixtral-multi"`
  - `"codellama-multi"`
  - `"mistral:7b-instruct-q5_K_M"`
- **Description**: The Ollama model identifier used for each agent
- **Research Note**: Enables cross-model experiments (e.g., Mixtral vs Llama3)

##### `config.decision_token_limit`
- **Type**: Integer
- **Default**: 256
- **Description**: Maximum tokens for agent decision responses
- **Purpose**: Prevents overly long responses, controls API costs

##### `config.reflection_token_limit`
- **Type**: Integer
- **Default**: 1024
- **Description**: Maximum tokens for post-episode reflection responses
- **Purpose**: Allows more detailed strategic analysis than decisions

##### `config.http_timeout`
- **Type**: Integer (seconds)
- **Default**: 60
- **Description**: HTTP request timeout for Ollama API calls
- **Purpose**: Prevents hanging on slow model responses

##### `config.force_decision_retries`
- **Type**: Integer
- **Default**: 2
- **Description**: Number of retry attempts when agent gives ambiguous decision
- **Purpose**: Ensures valid COOPERATE/DEFECT decisions in all rounds

---

### Aggregate Results

#### `elapsed_seconds`
- **Type**: Float
- **Example**: `243.7`
- **Description**: Total wall-clock time for the entire experiment
- **Usage**: Performance benchmarking, estimating cluster resource time

#### `agent_0` and `agent_1`
- **Type**: Object
- **Description**: Aggregate statistics for each agent across all episodes

```json
"agent_0": {
  "model": "llama3:8b-instruct-q5_K_M",
  "total_score": 285,
  "total_cooperations": 73,
  "overall_cooperation_rate": 0.73
}
```

##### `agent_X.model`
- **Type**: String
- **Description**: Model identifier for this agent (redundant with config but convenient)

##### `agent_X.total_score`
- **Type**: Integer
- **Description**: Sum of payoffs across all rounds in all episodes
- **Payoff Matrix** (standard IPD):
  - Mutual cooperation (C,C): 3 points each
  - Mutual defection (D,D): 1 point each
  - Exploitation (D,C): Defector gets 5, cooperator gets 0
  - Exploitation (C,D): Cooperator gets 0, defector gets 5

##### `agent_X.total_cooperations`
- **Type**: Integer
- **Description**: Total number of COOPERATE decisions across all rounds
- **Range**: 0 to `total_rounds`

##### `agent_X.overall_cooperation_rate`
- **Type**: Float (0.0 to 1.0)
- **Calculation**: `total_cooperations / total_rounds`
- **Interpretation**:
  - 0.0-0.3: Predominantly defection
  - 0.3-0.6: Mixed strategies
  - 0.6-0.8: Frequent cooperation
  - 0.8-1.0: Strong cooperation (possible TFT or GTFT)

---

### Episodes Array

#### `episodes`
- **Type**: Array of episode objects
- **Length**: Equal to `config.num_episodes`
- **Description**: Detailed round-by-round data for each episode

```json
"episodes": [
  {
    "episode": 1,
    "rounds": [ ... ],
    "agent_0": { ... },
    "agent_1": { ... }
  },
  ...
]
```

---

### Episode Object Structure

```json
{
  "episode": 1,
  "rounds": [ /* array of round objects */ ],
  "agent_0": {
    "episode_score": 57,
    "cooperations": 14,
    "cooperation_rate": 0.7,
    "reflection": "In this period, I observed..."
  },
  "agent_1": {
    "episode_score": 51,
    "cooperations": 13,
    "cooperation_rate": 0.65,
    "reflection": "My strategy evolved..."
  }
}
```

#### `episode`
- **Type**: Integer
- **Description**: Episode number (1-indexed)

#### `rounds`
- **Type**: Array of round objects
- **Length**: Equal to `config.rounds_per_episode`
- **Description**: Detailed information for each round within this episode

---

### Round Object Structure

```json
{
  "round": 1,
  "agent_0_action": "COOPERATE",
  "agent_1_action": "DEFECT",
  "agent_0_reasoning": "I will cooperate to establish...",
  "agent_1_reasoning": "Given the uncertainty...",
  "agent_0_payoff": 0,
  "agent_1_payoff": 5,
  "agent_0_episode_score": 0,
  "agent_1_episode_score": 5
}
```

#### `round`
- **Type**: Integer
- **Description**: Round number within the episode (1-indexed)

#### `agent_X_action`
- **Type**: String
- **Values**: `"COOPERATE"` or `"DEFECT"`
- **Description**: The decision made by the agent this round
- **Research Note**: The primary behavioral data for strategy analysis

#### `agent_X_reasoning`
- **Type**: String
- **Length**: Typically 50-250 characters (limited by decision_token_limit)
- **Description**: The agent's natural language explanation of their decision
- **Content Examples**:
  - Strategy articulation: "I will use tit-for-tat..."
  - Opponent modeling: "Since they defected last round..."
  - Learning: "This pattern suggests they are cooperative..."
- **Research Value**: Essential for interpretability and strategy classification

#### `agent_X_payoff`
- **Type**: Integer
- **Values**: 0, 1, 3, or 5 (based on standard IPD payoff matrix)
- **Description**: Points earned by this agent in this round
- **Calculation**:
  ```
  (C, C) → (3, 3)  # Reward for mutual cooperation
  (C, D) → (0, 5)  # Sucker's payoff vs Temptation
  (D, C) → (5, 0)  # Temptation vs Sucker's payoff
  (D, D) → (1, 1)  # Punishment for mutual defection
  ```

#### `agent_X_episode_score`
- **Type**: Integer
- **Description**: Cumulative score for this agent within the current episode up to and including this round
- **Usage**: Track within-episode score trajectories

---

### Episode-Level Agent Statistics

#### `agent_X.episode_score`
- **Type**: Integer
- **Description**: Total points earned by agent in this episode
- **Range**: `rounds_per_episode × 1` to `rounds_per_episode × 5`

#### `agent_X.cooperations`
- **Type**: Integer
- **Description**: Number of COOPERATE decisions in this episode
- **Range**: 0 to `rounds_per_episode`

#### `agent_X.cooperation_rate`
- **Type**: Float (0.0 to 1.0)
- **Calculation**: `cooperations / rounds_per_episode`
- **Research Usage**: Track cooperation trajectory across episodes

#### `agent_X.reflection`
- **Type**: String
- **Length**: Typically 200-1000 characters (limited by reflection_token_limit)
- **Description**: Agent's post-episode strategic reflection
- **Content Varies By** `reflection_type`:
  - **minimal**: Brief summary of performance
  - **standard**: Strategy identification, opponent analysis, future planning
  - **detailed**: Deep analysis including counterfactuals, confidence levels, multiple strategic scenarios
- **Research Value**: 
  - Evidence of learning and strategy evolution
  - Agent's theory of opponent's strategy
  - Metacognitive reasoning about cooperation

---

## Data Types Summary

| Field | Type | Typical Range | Key For |
|-------|------|---------------|---------|
| timestamp | string (ISO 8601) | - | Temporal tracking |
| hostname | string | - | Resource tracking |
| username | string | - | Accountability |
| host_0, host_1 | string | - | Cluster management |
| num_episodes | integer | 3-20 | Experimental design |
| rounds_per_episode | integer | 10-100 | Experimental design |
| temperature | float | 0.5-1.0 | LLM behavior |
| cooperation_rate | float | 0.0-1.0 | Primary outcome |
| total_score | integer | 100-500 | Payoff analysis |
| action | string | C or D | Behavioral data |
| reasoning | string | 50-250 chars | Interpretability |
| reflection | string | 200-1000 chars | Learning analysis |

---

## Common Analysis Queries

### Extract Cooperation Trajectory
```python
import json

with open('episodic_game_20250126_143045.json', 'r') as f:
    data = json.load(f)

cooperation_rates = [
    ep['agent_0']['cooperation_rate'] 
    for ep in data['episodes']
]
print(cooperation_rates)  # [0.35, 0.50, 0.70, 0.85, 0.90]
```

### Identify Strategy Patterns
```python
# Get all actions from episode 1
actions_0 = [
    r['agent_0_action'] 
    for r in data['episodes'][0]['rounds']
]
actions_1 = [
    r['agent_1_action'] 
    for r in data['episodes'][0]['rounds']
]

# Check for tit-for-tat pattern
def is_tft(my_actions, opp_actions):
    """Check if agent_0 mirrors opponent's previous action"""
    for i in range(1, len(my_actions)):
        if my_actions[i] != opp_actions[i-1]:
            return False
    return True
```

### Calculate Joint Payoff Efficiency
```python
# Maximum possible joint payoff is mutual cooperation
max_joint = data['config']['total_rounds'] * 6  # (3+3) per round

actual_joint = (
    data['agent_0']['total_score'] + 
    data['agent_1']['total_score']
)

efficiency = actual_joint / max_joint
print(f"Efficiency: {efficiency:.2%}")  # e.g., "Efficiency: 83%"
```

### Detect Cooperation Emergence
```python
# Find first episode with >70% cooperation
for ep in data['episodes']:
    if ep['agent_0']['cooperation_rate'] > 0.7:
        print(f"Cooperation emerged in episode {ep['episode']}")
        break
```

### Extract All Reasoning Text
```python
# Useful for qualitative analysis or NLP
all_reasoning = []
for episode in data['episodes']:
    for round_data in episode['rounds']:
        all_reasoning.append({
            'episode': episode['episode'],
            'round': round_data['round'],
            'agent_0': round_data['agent_0_reasoning'],
            'agent_1': round_data['agent_1_reasoning']
        })
```

---

## Research Applications

### For GENESIS Track (Moral Foundations)
- **Cooperation rate**: Proxy for Care/Harm and Fairness/Cheating dimensions
- **Reasoning text**: Evidence of moral reasoning (reciprocity, harm avoidance)
- **Reflection content**: Strategic vs. normative justifications
- **Episode trajectory**: Moral norm development over time

### For PRAXIS Track (Business Strategy)
- **Total scores**: Firm performance metrics
- **Cooperation emergence**: Trust-building in partnerships
- **Strategy patterns**: Competitive vs. cooperative dynamics
- **Temperature effects**: Risk tolerance in decision-making

### Methodological Considerations
- **Replication**: Same config should produce similar (but not identical) patterns
- **Random seeds**: Not currently logged (feature request?)
- **LLM nondeterminism**: Temperature > 0 means exact replication impossible
- **Episode learning**: Compare first vs. last episode cooperation rates

---

## File Size Considerations

Typical file sizes:
- **3 episodes × 10 rounds**: ~50-80 KB
- **5 episodes × 20 rounds**: ~150-250 KB
- **10 episodes × 50 rounds**: ~800 KB - 1.5 MB

Reasoning and reflection text dominate file size. For large-scale experiments:
- Consider reducing `reflection_token_limit` 
- Or store reflections separately
- Or compress/archive old experiments

---

## Version Information

**Current Version**: Generated by `episodic_ipd_game.py` as of January 2025

**Schema Stability**: This format is expected to remain stable. Any changes will be documented in:
- Git commit messages
- This reference document
- The main README

**Backward Compatibility**: Older JSON files (pre-January 2025) may lack:
- `username` field
- `host_0` and `host_1` fields
- `prompts` section
- Some `config` fields

---

## Questions or Issues?

If you encounter JSON files that don't match this specification:
1. Check the file's timestamp
2. Check the version of `episodic_ipd_game.py` used
3. Look for error messages in the corresponding `.log` file
4. Verify all experiments completed successfully

For research questions about interpreting results, consult:
- `README.md` - Project overview
- `docs/EXPERIMENTAL_DESIGN.md` - Research methodology
- Project documentation in `/mnt/project/`

---

**Last Updated**: January 26, 2025  
**Document Version**: 1.0  
**Author**: Doug Hart (dhart@regis.edu)
