DO $$
    BEGIN
        execute 'alter database '||current_database()||' set search_path = observations, admin, extensions, public';
    END
$$;
