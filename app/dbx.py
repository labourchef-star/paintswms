"""Tiny DB layer: Postgres (DATABASE_URL, e.g. Render free Postgres) or SQLite (DB_PATH) for local tests."""
import os, sqlite3
from contextlib import contextmanager
URL=os.environ.get("DATABASE_URL","")
PG=URL.startswith("postgres")
if PG:
    import psycopg
    from psycopg.rows import dict_row
class C:
    def __init__(s,raw): s.raw=raw
    def execute(s,sql,p=()):
        if PG:
            cur=s.raw.cursor(); cur.execute(sql.replace("?","%s"),p); return cur
        return s.raw.execute(sql,p)
    def executescript(s,sql):
        for st in [x.strip() for x in sql.split(";") if x.strip()]: s.execute(st)
@contextmanager
def db():
    if PG: raw=psycopg.connect(URL,row_factory=dict_row)
    else:
        raw=sqlite3.connect(os.environ.get("DB_PATH","/tmp/paintswms.db")); raw.row_factory=sqlite3.Row
    try: yield C(raw); raw.commit()
    finally: raw.close()
ID="serial primary key" if PG else "integer primary key"
SCHEMA=f"""
create table if not exists users(id {ID},email text unique,pro_until double precision default 0,license text,created double precision);
create table if not exists codes(email text,purpose text,hash text,exp double precision,tries int default 0,payload text);
create table if not exists sessions(tok text primary key,user_id int,exp double precision);
create table if not exists profiles(user_id int primary key,business text,abn text,contact text,phone text,crew text,equipment text,state text);
create table if not exists swms(id {ID},user_id int,data text,created double precision,updated double precision,paid int default 0);
create table if not exists signoffs(id {ID},swms_id int,name text,dt text);
create table if not exists hits(key text,kind text,ts double precision);
create table if not exists leads(email text,ts double precision,ip text,payload text);
create table if not exists pending(id text primary key,data text,ts double precision);
create table if not exists unlocks(key text primary key,swms_id int,user_id int,ts double precision);
create table if not exists counters(day text,event text,n int default 0,primary key(day,event));
create index if not exists hits_k on hits(key,kind,ts)
"""
