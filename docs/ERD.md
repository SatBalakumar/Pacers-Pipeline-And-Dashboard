# 📊 Pacers Analytics Database ERD

## Entity Relationship Diagram - Bronze → Silver → Gold Architecture

```mermaid
erDiagram
    %% ========================================
    %% BRONZE LAYER (Raw Data)
    %% ========================================
    
    BRONZE_SCHEDULE {
        string game_id PK
        string game_date
        string home_team
        string away_team
        string venue
        string game_status
    }
    
    BRONZE_PLAYERS {
        string player_id PK
        string full_name
        string team_abbreviation
        string position
        int height_inches
        int weight
        string country
    }
    
    BRONZE_BOXSCORES {
        string game_id PK
        string player_id PK
        string team_id
        int minutes
        int points
        int rebounds
        int assists
        float fg_pct
    }
    
    BRONZE_PBP {
        string game_id PK
        int period
        string pc_time
        string description
        string player1_id
        int home_score
        int away_score
    }

    %% ========================================
    %% SILVER LAYER (Cleaned & Validated)
    %% ========================================
    
    games_silver {
        string game_id PK
        datetime game_datetime_est
        string venue_name
        int venue_id FK
        int home_team_id FK
        int away_team_id FK
        int home_points
        int away_points
        string status_code
        int game_type_id FK
        string season
    }
    
    teams_silver {
        int team_id PK
        string team_name
        string team_abbreviation
        string team_city
        string team_conference
        string team_division
    }
    
    players_silver {
        int player_id PK
        string first_name
        string last_name
        string full_name
        int team_id FK
        int position_id FK
        int height_inches
        int weight
        int jersey_number
        int country_id FK
        date birth_date
    }
    
    venues_silver {
        int venue_id PK
        string venue_name
        string venue_city
        string venue_state
        string venue_country
    }
    
    positions_silver {
        int position_id PK
        string position_code
        string position_name
    }
    
    countries_silver {
        int country_id PK
        string country_name
        string country_code
    }
    
    gametypes_silver {
        int game_type_id PK
        string game_type_name
        string game_type_description
    }
    
    playerboxscore_silver {
        string game_id PK, FK
        int player_id PK, FK
        int team_id FK
        string player_name
        string position_code
        int minutes
        int pts
        int fgm
        int fga
        float fg_pct
        int fg3m
        int fg3a
        float fg3_pct
        int ftm
        int fta
        float ft_pct
        int reb
        int ast
        int stl
        int blk
        int tov
        int pf
        int plusminus
        boolean played_flag
    }
    
    gameteamtotals_silver {
        string game_id PK, FK
        int team_id PK, FK
        boolean is_home
        int pts
        int fgm
        int fga
        float fg_pct
        int fg3m
        int fg3a
        float fg3_pct
        int ftm
        int fta
        float ft_pct
        int reb
        int ast
        int stl
        int blk
        int tov
        int pf
    }
    
    draftpicks_silver {
        int player_id PK, FK
        int draft_year
        int draft_round
        int draft_number
        string draft_team
    }
    
    pbp_silver {
        string game_id PK, FK
        int event_num PK
        int period
        string pc_time
        string description
        int player1_id FK
        int player2_id FK
        int player3_id FK
        int home_score
        int away_score
        string home_description
        string visitor_description
        string neutral_description
    }
    
    status_codes_silver {
        string status_code PK
        string status_name
        string status_description
    }

    %% ========================================
    %% GOLD LAYER (Analytics & Business Logic)
    %% ========================================
    
    gold_games {
        string game_id PK, FK
        int team_id PK, FK
        datetime game_datetime_est
        string venue_name
        boolean is_home
        int pts
        int opp_pts
        string result
        string team_name_team
        string team_abbreviation_team
        string team_name_opp
        string team_abbreviation_opp
        int game_type_id
        string season
        string status_code
    }
    
    gold_game_summary {
        string game_id PK, FK
        datetime game_datetime_est
        string venue_name
        string home_team_abbreviation
        string away_team_abbreviation
        int home_points
        int away_points
        string status_code
        int game_type_id
        string season
    }
    
    gold_player_info {
        int player_id PK, FK
        string first_name
        string last_name
        string full_name
        int team_id FK
        string team_name_team
        string team_abbreviation_team
        string position_code
        int height_inches
        int weight
        int jersey_num
        string country_name
        date birth_date
        int draft_year
        int draft_round
        int draft_number
    }
    
    gold_player_boxscore {
        string game_id PK, FK
        int player_id PK, FK
        int team_id FK
        datetime game_datetime_est
        string team_abbreviation_team
        string position_code
        string player_name
        int minutes
        int pts
        int fgm
        int fga
        float fg_pct
        int fg3m
        int fg3a
        float fg3_pct
        int ftm
        int fta
        float ft_pct
        int reb
        int ast
        int stl
        int blk
        int tov
        int pf
        int plusminus
        boolean played_flag
    }
    
    gold_player_averages {
        int player_id PK, FK
        string season
        int gp
        float mpg
        float ppg
        float rpg
        float apg
        float spg
        float bpg
        float tpg
        float fg_pct
        float three_pct
        float ft_pct
    }

    %% ========================================
    %% GOLD VIEWS (Pacers-Specific)
    %% ========================================
    
    gold_pacers_games {
        string "*All gold_games columns*"
        string "WHERE team_abbreviation_team = 'IND'"
    }
    
    gold_pacers_players {
        string "*All gold_player_info columns*"
        string "WHERE team_abbreviation_team = 'IND'"
    }
    
    gold_pacers_season_averages {
        string "*gold_player_averages + player_info*"
        string "WHERE team_abbreviation_team = 'IND'"
    }
    
    gold_game_summary_with_status {
        string "*gold_game_summary + status_name*"
        string "JOIN status_codes_silver"
    }

    %% ========================================
    %% RELATIONSHIPS - SILVER LAYER
    %% ========================================
    
    %% Core Entity Relationships
    games_silver ||--o{ playerboxscore_silver : "has stats for"
    games_silver ||--o{ gameteamtotals_silver : "has team totals"
    games_silver ||--o{ pbp_silver : "has play-by-play"
    games_silver }o--|| venues_silver : "played at"
    games_silver }o--|| teams_silver : "home team"
    games_silver }o--|| teams_silver : "away team"
    games_silver }o--|| gametypes_silver : "game type"
    games_silver }o--|| status_codes_silver : "game status"
    
    %% Player Relationships
    players_silver ||--o{ playerboxscore_silver : "player stats"
    players_silver ||--o| draftpicks_silver : "draft info"
    players_silver }o--|| teams_silver : "plays for"
    players_silver }o--|| positions_silver : "plays position"
    players_silver }o--|| countries_silver : "from country"
    
    %% Team Relationships
    teams_silver ||--o{ playerboxscore_silver : "team stats"
    teams_silver ||--o{ gameteamtotals_silver : "team totals"
    
    %% Play-by-Play Relationships
    pbp_silver }o--|| players_silver : "player1"
    pbp_silver }o--|| players_silver : "player2"
    pbp_silver }o--|| players_silver : "player3"

    %% ========================================
    %% RELATIONSHIPS - GOLD LAYER
    %% ========================================
    
    %% Gold table relationships to Silver
    gold_games }o--|| games_silver : "based on"
    gold_games }o--|| teams_silver : "team info"
    gold_game_summary }o--|| games_silver : "game summary"
    gold_player_info }o--|| players_silver : "player data"
    gold_player_info }o--|| teams_silver : "team info"
    gold_player_info }o--|| positions_silver : "position info"
    gold_player_info }o--|| countries_silver : "country info"
    gold_player_info }o--|| draftpicks_silver : "draft info"
    
    gold_player_boxscore }o--|| playerboxscore_silver : "enhanced stats"
    gold_player_boxscore }o--|| games_silver : "game context"
    gold_player_boxscore }o--|| teams_silver : "team context"
    gold_player_boxscore }o--|| positions_silver : "position context"
    
    gold_player_averages }o--|| gold_player_boxscore : "aggregated from"
    
    %% Gold views relationships
    gold_pacers_games }o--|| gold_games : "filtered view"
    gold_pacers_players }o--|| gold_player_info : "filtered view"
    gold_pacers_season_averages }o--|| gold_player_averages : "joined view"
    gold_pacers_season_averages }o--|| gold_player_info : "joined view"
    gold_game_summary_with_status }o--|| gold_game_summary : "enhanced view"
    gold_game_summary_with_status }o--|| status_codes_silver : "status lookup"

    %% ========================================
    %% DATA FLOW TRANSFORMATION
    %% ========================================
    
    %% Bronze to Silver transformations
    BRONZE_SCHEDULE -.->|"Clean & Validate"| games_silver
    BRONZE_PLAYERS -.->|"Type & Schema"| players_silver
    BRONZE_BOXSCORES -.->|"Normalize Stats"| playerboxscore_silver
    BRONZE_PBP -.->|"Parse Events"| pbp_silver
    
    %% Silver to Gold transformations
    games_silver -.->|"Team Perspective"| gold_games
    games_silver -.->|"Game Summary"| gold_game_summary
    players_silver -.->|"Enhanced Joins"| gold_player_info
    playerboxscore_silver -.->|"Enriched Stats"| gold_player_boxscore
    gold_player_boxscore -.->|"Aggregations"| gold_player_averages
```

## 🏗️ Architecture Layers

### 🥉 **Bronze Layer (Raw Data)**
- **Purpose**: Raw NBA data files as ingested
- **Format**: Parquet files in `data/raw/`
- **Characteristics**: Unvalidated, original structure
- **Examples**: Schedule, Players, Boxscores, Play-by-Play

### 🥈 **Silver Layer (Cleaned & Validated)**
- **Purpose**: Cleaned, typed, and validated data
- **Format**: Parquet files + SQLite tables
- **Characteristics**: Proper schemas, nullable types, constraints
- **Key Tables**: 12 silver tables with referential integrity

### 🥇 **Gold Layer (Analytics Ready)**
- **Purpose**: Business-ready analytical tables and views
- **Format**: SQLite tables and views
- **Characteristics**: Joined data, aggregations, Pacers-focused
- **Key Assets**: 5 core tables + 10+ analytical views

## 🔗 Key Relationships

### **Primary Relationships**
1. **Games ← → Teams**: Many-to-many (home/away)
2. **Games → Player Stats**: One-to-many boxscore records
3. **Players → Teams**: Many-to-one team assignment
4. **Games → Play-by-Play**: One-to-many event records

### **Lookup Relationships**
- **Countries** → Players (origin)
- **Positions** → Players (role)
- **Venues** → Games (location)
- **Game Types** → Games (preseason/regular/playoff)
- **Status Codes** → Games (final/postponed/etc)

### **Gold Transformations**
- **Team Perspective**: `gold_games` (2 rows per game)
- **Enhanced Joins**: `gold_player_info` (players + team + position + country + draft)
- **Enriched Stats**: `gold_player_boxscore` (stats + game + team context)
- **Aggregations**: `gold_player_averages` (season-level summaries)

## 🏀 Pacers-Specific Views

### **Filtered Views**
- `gold_pacers_games` - Only Indiana Pacers games
- `gold_pacers_players` - Only current Pacers roster
- `gold_pacers_season_averages` - Only Pacers player stats

### **Enhanced Views**
- `gold_game_summary_with_status` - Games with readable status
- `gold_team_standings` - Win/loss records calculation

## 📊 Data Flow Summary

```
Raw NBA Data (Bronze)
        ↓ 
   Clean & Validate
        ↓
Typed Silver Tables ← → SQLite Database
        ↓
   Join & Aggregate  
        ↓
Gold Analytics Tables
        ↓
  Filter & Enhance
        ↓
Pacers-Focused Views → Streamlit Dashboard
```

## 🎯 Dashboard Integration

The **Streamlit Dashboard** primarily uses:
- `gold_pacers_games` - Game analysis
- `gold_pacers_players` - Player lookup  
- `gold_player_boxscore` - Boxscore browser
- `gold_game_summary_with_status` - Game summaries
- `gold_pacers_season_averages` - Season stats
- `pbp_silver` - Play-by-play analysis
- `teams_silver` - Team information

This ERD shows the complete data lineage from raw NBA files through the analytical dashboard! 🏀