CREATE TABLE public.download_videos (
    video_id uuid NOT NULL,
    link character varying NOT NULL,
    title character varying,
    quality character varying,
    task_begin timestamp without time zone,
    task_end timestamp without time zone,
    status integer NOT NULL,
    filename character varying NOT NULL,
    filesize bigint
);


CREATE TABLE public.videos (
    output_filename character varying NOT NULL,
    source character varying NOT NULL,
    status integer NOT NULL,
    progress integer,
    task_begin timestamp without time zone,
    task_end timestamp without time zone,
    description TEXT DEFAULT '' NOT NULL
);

CREATE TABLE records (
    video_id UUID NOT NULL,
    output_name VARCHAR NOT NULL,
    title VARCHAR,
    type VARCHAR NOT NULL,
    source_name VARCHAR NOT NULL,
    status INTEGER NOT NULL,
    task_begin TIMESTAMP WITHOUT TIME ZONE,
    task_end TIMESTAMP WITHOUT TIME ZONE,
    progress INTEGER,
    PRIMARY KEY (video_id)
);

ALTER TABLE ONLY public.download_videos
    ADD CONSTRAINT download_videos_pkey PRIMARY KEY (video_id);

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_pkey PRIMARY KEY (output_filename);