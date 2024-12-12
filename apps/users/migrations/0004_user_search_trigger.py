from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_role_user_failed_login_attempts_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            CREATE EXTENSION IF NOT EXISTS pg_trgm;
            
            CREATE OR REPLACE FUNCTION users_update_search_vector_trigger() RETURNS trigger AS $$
            begin
                new.search_vector := setweight(to_tsvector('simple', coalesce(new.username, '')), 'A') ||
                                   setweight(to_tsvector('simple', coalesce(new.email, '')), 'B') ||
                                   setweight(to_tsvector('simple', coalesce(new.first_name, '')), 'C') ||
                                   setweight(to_tsvector('simple', coalesce(new.last_name, '')), 'C');
                return new;
            end
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS users_search_vector_update ON users_user;
            CREATE TRIGGER users_search_vector_update
                BEFORE INSERT OR UPDATE
                ON users_user
                FOR EACH ROW
                EXECUTE FUNCTION users_update_search_vector_trigger();
            ''',
            reverse_sql='''
            DROP TRIGGER IF EXISTS users_search_vector_update ON users_user;
            DROP FUNCTION IF EXISTS users_update_search_vector_trigger();
            DROP EXTENSION IF EXISTS pg_trgm;
            '''
        ),
        # Cập nhật search_vector cho dữ liệu hiện có
        migrations.RunSQL(
            sql='''
            UPDATE users_user
            SET search_vector = setweight(to_tsvector('simple', coalesce(username, '')), 'A') ||
                              setweight(to_tsvector('simple', coalesce(email, '')), 'B') ||
                              setweight(to_tsvector('simple', coalesce(first_name, '')), 'C') ||
                              setweight(to_tsvector('simple', coalesce(last_name, '')), 'C');
            ''',
            reverse_sql='''
            UPDATE users_user SET search_vector = NULL;
            '''
        ),
    ] 