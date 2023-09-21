select 'create database kg_integration' where not exists (select from pg_database where datname = 'kg_integration')\gexec
