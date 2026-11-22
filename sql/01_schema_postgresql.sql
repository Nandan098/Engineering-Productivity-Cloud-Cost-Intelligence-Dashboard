-- PostgreSQL schema for the synthetic Engineering Analytics portfolio project.
-- Execute from the project root before loading the CSVs.

DROP TABLE IF EXISTS incidents CASCADE;
DROP TABLE IF EXISTS capacity CASCADE;
DROP TABLE IF EXISTS cloud_costs CASCADE;
DROP TABLE IF EXISTS deployments CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS sprints CASCADE;
DROP TABLE IF EXISTS engineers CASCADE;
DROP TABLE IF EXISTS teams CASCADE;

CREATE TABLE teams (
    team_id VARCHAR(8) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    domain VARCHAR(80),
    headcount INTEGER NOT NULL CHECK (headcount > 0),
    manager_role VARCHAR(80),
    monthly_cloud_budget_inr NUMERIC(14,2),
    reporting_location VARCHAR(80)
);

CREATE TABLE engineers (
    engineer_id VARCHAR(10) PRIMARY KEY,
    team_id VARCHAR(8) NOT NULL REFERENCES teams(team_id),
    role VARCHAR(100),
    career_level VARCHAR(20),
    experience_years INTEGER,
    employment_type VARCHAR(20),
    standard_weekly_hours INTEGER
);

CREATE TABLE sprints (
    sprint_id VARCHAR(20) PRIMARY KEY,
    team_id VARCHAR(8) NOT NULL REFERENCES teams(team_id),
    sprint_number INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    planned_capacity_hours NUMERIC(12,2),
    sprint_goal VARCHAR(150),
    UNIQUE(team_id, sprint_number),
    CHECK (end_date >= start_date)
);

CREATE TABLE tasks (
    task_id VARCHAR(12) PRIMARY KEY,
    team_id VARCHAR(8) NOT NULL REFERENCES teams(team_id),
    sprint_id VARCHAR(20) NOT NULL REFERENCES sprints(sprint_id),
    assignee_id VARCHAR(10) REFERENCES engineers(engineer_id),
    task_type VARCHAR(30),
    priority VARCHAR(20),
    status VARCHAR(20),
    story_points INTEGER,
    is_committed BOOLEAN,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP NULL,
    last_updated_at TIMESTAMP,
    blocked_days INTEGER,
    cycle_time_days NUMERIC(8,2)
);

CREATE TABLE deployments (
    deployment_id VARCHAR(12) PRIMARY KEY,
    team_id VARCHAR(8) NOT NULL REFERENCES teams(team_id),
    engineer_id VARCHAR(10) REFERENCES engineers(engineer_id),
    service_name VARCHAR(100),
    environment VARCHAR(20),
    deployed_at TIMESTAMP,
    status VARCHAR(20),
    duration_minutes NUMERIC(8,1),
    rollback_flag BOOLEAN,
    commit_count INTEGER,
    is_emergency BOOLEAN
);

CREATE TABLE cloud_costs (
    cost_id VARCHAR(14) PRIMARY KEY,
    date DATE NOT NULL,
    team_id VARCHAR(8) NOT NULL REFERENCES teams(team_id),
    service_name VARCHAR(100),
    environment VARCHAR(20),
    cost_inr NUMERIC(14,2),
    budget_inr NUMERIC(14,2),
    currency VARCHAR(3)
);

CREATE TABLE capacity (
    date DATE NOT NULL,
    team_id VARCHAR(8) NOT NULL REFERENCES teams(team_id),
    active_headcount INTEGER,
    available_hours NUMERIC(10,2),
    logged_hours NUMERIC(10,2),
    delivery_hours NUMERIC(10,2),
    support_hours NUMERIC(10,2),
    incident_hours NUMERIC(10,2),
    meeting_and_admin_hours NUMERIC(10,2),
    overtime_hours NUMERIC(10,2),
    PRIMARY KEY(date, team_id)
);

CREATE TABLE incidents (
    incident_id VARCHAR(12) PRIMARY KEY,
    team_id VARCHAR(8) NOT NULL REFERENCES teams(team_id),
    service_name VARCHAR(100),
    started_at TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    severity VARCHAR(5),
    category VARCHAR(30),
    status VARCHAR(20),
    affected_users_estimate INTEGER,
    customer_impact_minutes INTEGER,
    related_deployment_id VARCHAR(12) REFERENCES deployments(deployment_id),
    suspected_change_related BOOLEAN
);

CREATE INDEX idx_engineers_team ON engineers(team_id);
CREATE INDEX idx_sprints_team_dates ON sprints(team_id, start_date, end_date);
CREATE INDEX idx_tasks_team_sprint ON tasks(team_id, sprint_id);
CREATE INDEX idx_deployments_team_date ON deployments(team_id, deployed_at);
CREATE INDEX idx_cloud_costs_team_date ON cloud_costs(team_id, date);
CREATE INDEX idx_capacity_team_date ON capacity(team_id, date);
CREATE INDEX idx_incidents_team_started ON incidents(team_id, started_at);
