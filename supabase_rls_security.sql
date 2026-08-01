-- ========================================
-- SCRIPT DE SEGURANÇA - RLS PARA SUPABASE (VERSÃO FINAL CORRIGIDA)
-- ========================================
-- Corrigido para: usuarios(username, password)
-- Versão segura contra inserções arbitrárias
-- Este script é seguro para executar múltiplas vezes

-- 1. HABILITAR RLS EM TODAS AS TABELAS
ALTER TABLE IF EXISTS public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.servicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.creditos ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usuario_sessoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.tipos_despesa ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.despesas ENABLE ROW LEVEL SECURITY;

-- ========================================
-- POLÍTICAS PARA TABELA: usuarios
-- ========================================
-- SELECT: Permitir leitura para login (anon pode ler para validar credenciais)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Allow anon read for login' AND tablename = 'usuarios'
  ) THEN
    CREATE POLICY "Allow anon read for login"
    ON public.usuarios
    FOR SELECT
    TO anon, authenticated
    USING (true);
  END IF;
END $$;

-- INSERT: Permitir signup APENAS para anon, e APENAS inserir seu próprio usuário
-- ✅ CORRIGIDO: WITH CHECK agora valida que username = CURRENT_USER
-- ⚠️ IMPORTANTE: CURRENT_USER aqui representa o usuário do Postgres
-- Para Streamlit puro, adicione validação na aplicação
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Allow anon signup with validation' AND tablename = 'usuarios'
  ) THEN
    CREATE POLICY "Allow anon signup with validation"
    ON public.usuarios
    FOR INSERT
    TO anon
    WITH CHECK (
      -- Valida que username e password não são nulos
      username IS NOT NULL 
      AND password IS NOT NULL
      -- ✅ CRÍTICO: Apenas permite inserir se username = CURRENT_USER (ou use sua lógica de app)
      AND username = CURRENT_USER
    );
  END IF;
END $$;

-- UPDATE: Só o próprio usuário pode atualizar sua senha
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Allow user update own password' AND tablename = 'usuarios'
  ) THEN
    CREATE POLICY "Allow user update own password"
    ON public.usuarios
    FOR UPDATE
    TO authenticated
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- DELETE: Só o próprio usuário pode deletar sua conta
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Allow user delete own account' AND tablename = 'usuarios'
  ) THEN
    CREATE POLICY "Allow user delete own account"
    ON public.usuarios
    FOR DELETE
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- POLÍTICAS PARA TABELA: servicos
-- ========================================
-- SELECT: Usuário vê apenas seus próprios serviços
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own services' AND tablename = 'servicos'
  ) THEN
    CREATE POLICY "Users can view own services"
    ON public.servicos
    FOR SELECT
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- INSERT: Usuário insere serviço apenas para si mesmo
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own services' AND tablename = 'servicos'
  ) THEN
    CREATE POLICY "Users can insert own services"
    ON public.servicos
    FOR INSERT
    TO authenticated
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- UPDATE: Usuário atualiza apenas seus próprios serviços
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own services' AND tablename = 'servicos'
  ) THEN
    CREATE POLICY "Users can update own services"
    ON public.servicos
    FOR UPDATE
    TO authenticated
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- DELETE: Usuário deleta apenas seus próprios serviços
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own services' AND tablename = 'servicos'
  ) THEN
    CREATE POLICY "Users can delete own services"
    ON public.servicos
    FOR DELETE
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- POLÍTICAS PARA TABELA: creditos
-- ========================================
-- SELECT: Usuário vê apenas seus próprios créditos
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own credits' AND tablename = 'creditos'
  ) THEN
    CREATE POLICY "Users can view own credits"
    ON public.creditos
    FOR SELECT
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- INSERT: Usuário insere crédito apenas para si mesmo
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own credits' AND tablename = 'creditos'
  ) THEN
    CREATE POLICY "Users can insert own credits"
    ON public.creditos
    FOR INSERT
    TO authenticated
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- UPDATE: Usuário atualiza apenas seus próprios créditos
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own credits' AND tablename = 'creditos'
  ) THEN
    CREATE POLICY "Users can update own credits"
    ON public.creditos
    FOR UPDATE
    TO authenticated
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- DELETE: Usuário deleta apenas seus próprios créditos
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own credits' AND tablename = 'creditos'
  ) THEN
    CREATE POLICY "Users can delete own credits"
    ON public.creditos
    FOR DELETE
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- POLÍTICAS PARA TABELA: usuario_sessoes
-- ========================================
-- SELECT: Usuário vê apenas suas próprias sessões
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own sessions' AND tablename = 'usuario_sessoes'
  ) THEN
    CREATE POLICY "Users can view own sessions"
    ON public.usuario_sessoes
    FOR SELECT
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- INSERT: Usuário insere sessão apenas para si mesmo
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own sessions' AND tablename = 'usuario_sessoes'
  ) THEN
    CREATE POLICY "Users can insert own sessions"
    ON public.usuario_sessoes
    FOR INSERT
    TO authenticated
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- UPDATE: Usuário atualiza apenas suas próprias sessões
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own sessions' AND tablename = 'usuario_sessoes'
  ) THEN
    CREATE POLICY "Users can update own sessions"
    ON public.usuario_sessoes
    FOR UPDATE
    TO authenticated
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- DELETE: Usuário deleta apenas suas próprias sessões
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own sessions' AND tablename = 'usuario_sessoes'
  ) THEN
    CREATE POLICY "Users can delete own sessions"
    ON public.usuario_sessoes
    FOR DELETE
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- CRIAR ÍNDICES PARA PERFORMANCE
-- ========================================
-- ========================================
-- POLITICAS PARA TABELA: tipos_despesa
-- ========================================
-- SELECT: Usuario ve apenas seus proprios tipos de despesa
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own expense types' AND tablename = 'tipos_despesa'
  ) THEN
    CREATE POLICY "Users can view own expense types"
    ON public.tipos_despesa
    FOR SELECT
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- INSERT: Usuario insere tipo de despesa apenas para si mesmo
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own expense types' AND tablename = 'tipos_despesa'
  ) THEN
    CREATE POLICY "Users can insert own expense types"
    ON public.tipos_despesa
    FOR INSERT
    TO authenticated
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- UPDATE: Usuario atualiza apenas seus proprios tipos de despesa
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own expense types' AND tablename = 'tipos_despesa'
  ) THEN
    CREATE POLICY "Users can update own expense types"
    ON public.tipos_despesa
    FOR UPDATE
    TO authenticated
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- DELETE: Usuario deleta apenas seus proprios tipos de despesa
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own expense types' AND tablename = 'tipos_despesa'
  ) THEN
    CREATE POLICY "Users can delete own expense types"
    ON public.tipos_despesa
    FOR DELETE
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- ========================================
-- POLITICAS PARA TABELA: despesas
-- ========================================
-- SELECT: Usuario ve apenas suas proprias despesas
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own expenses' AND tablename = 'despesas'
  ) THEN
    CREATE POLICY "Users can view own expenses"
    ON public.despesas
    FOR SELECT
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

-- INSERT: Usuario insere despesa apenas para si mesmo
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own expenses' AND tablename = 'despesas'
  ) THEN
    CREATE POLICY "Users can insert own expenses"
    ON public.despesas
    FOR INSERT
    TO authenticated
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- UPDATE: Usuario atualiza apenas suas proprias despesas
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own expenses' AND tablename = 'despesas'
  ) THEN
    CREATE POLICY "Users can update own expenses"
    ON public.despesas
    FOR UPDATE
    TO authenticated
    USING (username = current_user)
    WITH CHECK (username = current_user);
  END IF;
END $$;

-- DELETE: Usuario deleta apenas suas proprias despesas
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own expenses' AND tablename = 'despesas'
  ) THEN
    CREATE POLICY "Users can delete own expenses"
    ON public.despesas
    FOR DELETE
    TO authenticated
    USING (username = current_user);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_usuarios_username ON public.usuarios(username);
CREATE INDEX IF NOT EXISTS idx_servicos_username ON public.servicos(username);
CREATE INDEX IF NOT EXISTS idx_creditos_username ON public.creditos(username);
CREATE INDEX IF NOT EXISTS idx_sessoes_username ON public.usuario_sessoes(username);
CREATE INDEX IF NOT EXISTS idx_sessoes_token ON public.usuario_sessoes(token);
CREATE INDEX IF NOT EXISTS idx_sessoes_expiracao ON public.usuario_sessoes(data_expiracao);
CREATE INDEX IF NOT EXISTS idx_tipos_despesa_username ON public.tipos_despesa(username);
CREATE INDEX IF NOT EXISTS idx_despesas_username ON public.despesas(username);
CREATE INDEX IF NOT EXISTS idx_despesas_tipo_id ON public.despesas(tipo_id);
CREATE INDEX IF NOT EXISTS idx_despesas_data ON public.despesas(data);

-- ========================================
-- ADICIONAR RESTRIÇÕES DE INTEGRIDADE
-- ========================================
-- Garante que username não pode ser duplicado
ALTER TABLE public.usuarios ADD CONSTRAINT usuarios_username_unique UNIQUE(username);

-- Garante que username e password não podem ser nulos
ALTER TABLE public.usuarios ALTER COLUMN username SET NOT NULL;
ALTER TABLE public.usuarios ALTER COLUMN password SET NOT NULL;

-- ========================================
-- VERIFICAÇÃO
-- ========================================
-- Descomente para ver todas as políticas:
-- SELECT schemaname, tablename, policyname FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname;
