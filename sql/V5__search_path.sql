DO $$
    BEGIN
        EXECUTE 'ALTER DATABASE '||current_database()||' SET search_path = observations, admin, extensions, public';
    END
$$;
