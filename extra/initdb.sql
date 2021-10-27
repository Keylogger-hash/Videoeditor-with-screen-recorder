CREATE TABLE public.download_videos (
    video_id uuid NOT NULL,
    link character varying NOT NULL,
    title character varying,
    quality character varying,
    task_begin timestamp without time zone,
    task_end timestamp without time zone,
    status integer NOT NULL,
    filename character varying NOT NULL
);


CREATE TABLE public.videos (
    output_filename character varying NOT NULL,
    source character varying NOT NULL,
    status integer NOT NULL,
    progress integer,
    task_begin timestamp without time zone,
    task_end timestamp without time zone
);

ALTER TABLE ONLY public.download_videos
    ADD CONSTRAINT download_videos_pkey PRIMARY KEY (video_id);

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_pkey PRIMARY KEY (output_filename);