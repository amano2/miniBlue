import { createClient } from '@supabase/supabase-js';

export const SUPABASE_URL = 'https://mtodhmyaikedwojxhsfw.supabase.co';
export const SUPABASE_ANON_KEY =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10b2RobXlhaWtlZHdvanhoc2Z3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ1NjM4NDgsImV4cCI6MjExMDEzOTg0OH0.nqqX6q-ykiaj-zXoyRlMFiRnQ4BkxgkvyXe70-4wQcM';
export const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_WavPmJsGGy82nY3DzqaU3g_yPWy2GFY';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});
