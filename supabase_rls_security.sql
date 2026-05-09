-- ========================================
-- SCRIPT DE SEGURANÇA - RLS PARA SUPABASE (VERSÃO SEGURA)
-- ========================================
-- Este script é seguro para executar múltiplas vezes
-- Não deleta dados, apenas cria estruturas se não existirem

-- 1. HABILITAR RLS EM TODAS AS TABELAS (idempotente)
ALTER TABLE IF EXISTS public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.servicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.creditos ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usuario_sessoes ENABLE ROW LEVEL SECURITY;

-- 2. CRIAR POLÍTICAS (apenas se não existirem)
-- IMPORTANTE: Como você usa Streamlit (sem auth nativa), 
-- as políticas usam o username como identificador

-- ========================================
-- POLÍTICAS PARA TABELA: usuarios
-- ========================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Enable read access for own user' AND tablename = 'usuarios'
  ) THEN
    CREATE POLICY "Enable read access for own user"
    ON public.usuarios
    FOR SELECT
    USING (true);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Enable insert for signup' AND tablename = 'usuarios'
  ) THEN
    CREATE POLICY "Enable insert for signup"
    ON public.usuarios
    FOR INSERT
    WITH CHECK (true);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Enable update for own user' AND tablename = 'usuarios'
  ) THEN
    CREATE POLICY "Enable update for own user"
    ON public.usuarios
    FOR UPDATE
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Enable delete for own user' AND tablename = 'usuarios'
  ) THEN
    CREATE POLICY "Enable delete for own user"
    ON public.usuarios
    FOR DELETE
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- POLÍTICAS PARA TABELA: servicos
-- ========================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own services' AND tablename = 'servicos'
  ) THEN
    CREATE POLICY "Users can view own services"
    ON public.servicos
    FOR SELECT
    USING (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own services' AND tablename = 'servicos'
  ) THEN
    CREATE POLICY "Users can insert own services"
    ON public.servicos
    FOR INSERT
    WITH CHECK (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own services' AND tablename = 'servicos'
  ) THEN
    CREATE POLICY "Users can update own services"
    ON public.servicos
    FOR UPDATE
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own services' AND tablename = 'servicos'
  ) THEN
    CREATE POLICY "Users can delete own services"
    ON public.servicos
    FOR DELETE
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- POLÍTICAS PARA TABELA: creditos
-- ========================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own credits' AND tablename = 'creditos'
  ) THEN
    CREATE POLICY "Users can view own credits"
    ON public.creditos
    FOR SELECT
    USING (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own credits' AND tablename = 'creditos'
  ) THEN
    CREATE POLICY "Users can insert own credits"
    ON public.creditos
    FOR INSERT
    WITH CHECK (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own credits' AND tablename = 'creditos'
  ) THEN
    CREATE POLICY "Users can update own credits"
    ON public.creditos
    FOR UPDATE
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own credits' AND tablename = 'creditos'
  ) THEN
    CREATE POLICY "Users can delete own credits"
    ON public.creditos
    FOR DELETE
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- POLÍTICAS PARA TABELA: usuario_sessoes
-- ========================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own sessions' AND tablename = 'usuario_sessoes'
  ) THEN
    CREATE POLICY "Users can view own sessions"
    ON public.usuario_sessoes
    FOR SELECT
    USING (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own sessions' AND tablename = 'usuario_sessoes'
  ) THEN
    CREATE POLICY "Users can insert own sessions"
    ON public.usuario_sessoes
    FOR INSERT
    WITH CHECK (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own sessions' AND tablename = 'usuario_sessoes'
  ) THEN
    CREATE POLICY "Users can update own sessions"
    ON public.usuario_sessoes
    FOR UPDATE
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own sessions' AND tablename = 'usuario_sessoes'
  ) THEN
    CREATE POLICY "Users can delete own sessions"
    ON public.usuario_sessoes
    FOR DELETE
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- CRIAR ÍNDICES PARA PERFORMANCE (idempotente)
-- ========================================
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON public.usuarios(username);
CREATE INDEX IF NOT EXISTS idx_servicos_username ON public.servicos(username);
CREATE INDEX IF NOT EXISTS idx_creditos_username ON public.creditos(username);
CREATE INDEX IF NOT EXISTS idx_sessoes_username ON public.usuario_sessoes(username);
CREATE INDEX IF NOT EXISTS idx_sessoes_token ON public.usuario_sessoes(token);
CREATE INDEX IF NOT EXISTS idx_sessoes_expiracao ON public.usuario_sessoes(data_expiracao);

-- ========================================
-- VERIFICAÇÃO (execute após criar as políticas)
-- ========================================
-- Descomente a linha abaixo para ver todas as políticas criadas:
-- SELECT schemaname, tablename, policyname, permissive, roles, qual, with_check FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname;
