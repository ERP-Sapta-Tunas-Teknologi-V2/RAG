from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_SECRET_KEY

supabase_admin = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)