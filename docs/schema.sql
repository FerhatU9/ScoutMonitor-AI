--
-- PostgreSQL database dump
--

\restrict dtuGCOZ1Y6mbfU4STGOCYvtjQMPlTKEbEkdj4j5RsdifXVkQvPfrcIvsGHSAcy7

-- Dumped from database version 18.7
-- Dumped by pg_dump version 18.7

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_reports (
    report_id bigint NOT NULL,
    player_id bigint NOT NULL,
    team_id bigint NOT NULL,
    season_id bigint NOT NULL,
    snapshot_date date NOT NULL,
    model_name text NOT NULL,
    report_data jsonb NOT NULL,
    validation_status text NOT NULL,
    review_status text DEFAULT 'PENDING'::text NOT NULL,
    reviewer_name text,
    review_notes text,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ai_reports_report_data_check CHECK ((jsonb_typeof(report_data) = 'object'::text)),
    CONSTRAINT ai_reports_review_status_check CHECK ((review_status = ANY (ARRAY['PENDING'::text, 'APPROVED'::text, 'REJECTED'::text]))),
    CONSTRAINT ai_reports_validation_status_check CHECK ((validation_status = ANY (ARRAY['PASS'::text, 'REVIEW_REQUIRED'::text]))),
    CONSTRAINT approved_only_if_valid CHECK (((review_status <> 'APPROVED'::text) OR (validation_status = 'PASS'::text))),
    CONSTRAINT review_decision_complete CHECK ((((review_status = 'PENDING'::text) AND (reviewer_name IS NULL) AND (reviewed_at IS NULL)) OR ((review_status = ANY (ARRAY['APPROVED'::text, 'REJECTED'::text])) AND (reviewer_name IS NOT NULL) AND (reviewed_at IS NOT NULL))))
);


--
-- Name: ai_reports_report_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.ai_reports ALTER COLUMN report_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ai_reports_report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: performance_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_alerts (
    alert_id bigint NOT NULL,
    player_id bigint NOT NULL,
    team_id bigint NOT NULL,
    season_id bigint NOT NULL,
    previous_snapshot_date date NOT NULL,
    current_snapshot_date date NOT NULL,
    goals_increase integer NOT NULL,
    assists_increase integer NOT NULL,
    message text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT performance_alerts_assists_increase_check CHECK ((assists_increase >= 0)),
    CONSTRAINT performance_alerts_goals_increase_check CHECK ((goals_increase >= 0)),
    CONSTRAINT positive_change CHECK (((goals_increase > 0) OR (assists_increase > 0))),
    CONSTRAINT valid_alert_dates CHECK ((current_snapshot_date > previous_snapshot_date))
);


--
-- Name: performance_alerts_alert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.performance_alerts ALTER COLUMN alert_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.performance_alerts_alert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: player_season_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.player_season_stats (
    player_id bigint NOT NULL,
    team_id bigint NOT NULL,
    season_id bigint NOT NULL,
    snapshot_date date DEFAULT CURRENT_DATE NOT NULL,
    goals integer,
    assists integer,
    retrieved_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT player_season_stats_assists_check CHECK ((assists >= 0)),
    CONSTRAINT player_season_stats_goals_check CHECK ((goals >= 0))
);


--
-- Name: player_stat_observations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.player_stat_observations (
    player_id bigint NOT NULL,
    team_id bigint NOT NULL,
    season_id bigint NOT NULL,
    snapshot_date date NOT NULL,
    goals integer,
    assists integer,
    data_status text NOT NULL,
    collected_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT player_stat_observations_assists_check CHECK ((assists >= 0)),
    CONSTRAINT player_stat_observations_data_status_check CHECK ((data_status = ANY (ARRAY['COMPLETE'::text, 'PARTIAL'::text, 'NOT_REPORTED'::text]))),
    CONSTRAINT player_stat_observations_goals_check CHECK ((goals >= 0))
);


--
-- Name: players; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.players (
    player_id bigint NOT NULL,
    name character varying(150) NOT NULL,
    team_id bigint,
    jersey_number integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: ai_reports ai_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_reports
    ADD CONSTRAINT ai_reports_pkey PRIMARY KEY (report_id);


--
-- Name: performance_alerts performance_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_alerts
    ADD CONSTRAINT performance_alerts_pkey PRIMARY KEY (alert_id);


--
-- Name: player_season_stats player_season_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_season_stats
    ADD CONSTRAINT player_season_stats_pkey PRIMARY KEY (player_id, team_id, season_id, snapshot_date);


--
-- Name: player_stat_observations player_stat_observations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_stat_observations
    ADD CONSTRAINT player_stat_observations_pkey PRIMARY KEY (player_id, team_id, season_id, snapshot_date);


--
-- Name: players players_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_pkey PRIMARY KEY (player_id);


--
-- Name: performance_alerts unique_performance_alert; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_alerts
    ADD CONSTRAINT unique_performance_alert UNIQUE (player_id, team_id, season_id, previous_snapshot_date, current_snapshot_date);


--
-- Name: unique_player_snapshot_report; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX unique_player_snapshot_report ON public.ai_reports USING btree (player_id, team_id, season_id, snapshot_date);


--
-- Name: ai_reports ai_reports_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_reports
    ADD CONSTRAINT ai_reports_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(player_id);


--
-- Name: performance_alerts performance_alerts_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_alerts
    ADD CONSTRAINT performance_alerts_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(player_id);


--
-- Name: player_season_stats player_season_stats_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_season_stats
    ADD CONSTRAINT player_season_stats_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(player_id);


--
-- Name: player_stat_observations player_stat_observations_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_stat_observations
    ADD CONSTRAINT player_stat_observations_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(player_id);


--
-- PostgreSQL database dump complete
--

\unrestrict dtuGCOZ1Y6mbfU4STGOCYvtjQMPlTKEbEkdj4j5RsdifXVkQvPfrcIvsGHSAcy7