-- ========================================
-- SCRIPT DE SEGURANÇA - RLS PARA SUPABASE
-- ========================================
-- Execute este script completo no SQL Editor do Supabase

-- 1. HABILITAR RLS EM TODAS AS TABELAS
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.servicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.creditos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuario_sessoes ENABLE ROW LEVEL SECURITY;

-- 2. DROPEAR POLÍTICAS ANTIGAS (se existirem)
DROP POLICY IF EXISTS "Users can view own row" ON public.usuarios;
DROP POLICY IF EXISTS "Users can update own row" ON public.usuarios;
DROP POLICY IF EXISTS "Users can delete own row" ON public.usuarios;
DROP POLICY IF EXISTS "Allow public signup" ON public.usuarios;

DROP POLICY IF EXISTS "Users can view own services" ON public.servicos;
DROP POLICY IF EXISTS "Users can insert own services" ON public.servicos;
DROP POLICY IF EXISTS "Users can update own services" ON public.servicos;
DROP POLICY IF EXISTS "Users can delete own services" ON public.servicos;

DROP POLICY IF EXISTS "Users can view own credits" ON public.creditos;
DROP POLICY IF EXISTS "Users can insert own credits" ON public.creditos;
DROP POLICY IF EXISTS "Users can update own credits" ON public.creditos;
DROP POLICY IF EXISTS "Users can delete own credits" ON public.creditos;

DROP POLICY IF EXISTS "Users can view own sessions" ON public.usuario_sessoes;
DROP POLICY IF EXISTS "Users can insert own sessions" ON public.usuario_sessoes;
DROP POLICY IF EXISTS "Users can update own sessions" ON public.usuario_sessoes;
DROP POLICY IF EXISTS "Users can delete own sessions" ON public.usuario_sessoes;

-- ========================================
-- POLÍTICAS PARA TABELA: usuarios
-- ========================================
-- IMPORTANTE: Como você usa Streamlit (sem auth nativa), 
-- as políticas usam o username como identificador

CREATE POLICY "Enable read access for own user"
ON public.usuarios
FOR SELECT
USING (true);  -- Permite leitura (necessário para login)

CREATE POLICY "Enable insert for signup"
ON public.usuarios
FOR INSERT
WITH CHECK (true);  -- Permite cadastro público

CREATE POLICY "Enable update for own user"
ON public.usuarios
FOR UPDATE
USING (username = current_user)
WITH CHECK (username = current_user);

CREATE POLICY "Enable delete for own user"
ON public.usuarios
FOR DELETE
USING (username = current_user);

-- ========================================
-- POLÍTICAS PARA TABELA: servicos
-- ========================================
CREATE POLICY "Users can view own services"
ON public.servicos
FOR SELECT
USING (username = current_user);

CREATE POLICY "Users can insert own services"
ON public.servicos
FOR INSERT
WITH CHECK (username = current_user);

CREATE POLICY "Users can update own services"
ON public.servicos
FOR UPDATE
USING (username = current_user)
WITH CHECK (username = current_user);

CREATE POLICY "Users can delete own services"
ON public.servicos
FOR DELETE
USING (username = current_user);

-- ========================================
-- POLÍTICAS PARA TABELA: creditos
-- ========================================
CREATE POLICY "Users can view own credits"
ON public.creditos
FOR SELECT
USING (username = current_user);

CREATE POLICY "Users can insert own credits"
ON public.creditos
FOR INSERT
WITH CHECK (username = current_user);

CREATE POLICY "Users can update own credits"
ON public.creditos
FOR UPDATE
USING (username = current_user)
WITH CHECK (username = current_user);

CREATE POLICY "Users can delete own credits"
ON public.creditos
FOR DELETE
USING (username = current_user);

-- ========================================
-- POLÍTICAS PARA TABELA: usuario_sessoes
-- ========================================
CREATE POLICY "Users can view own sessions"
ON public.usuario_sessoes
FOR SELECT
USING (username = current_user);

CREATE POLICY "Users can insert own sessions"
ON public.usuario_sessoes
FOR INSERT
WITH CHECK (username = current_user);

CREATE POLICY "Users can update own sessions"
ON public.usuario_sessoes
FOR UPDATE
USING (username = current_user)
WITH CHECK (username = current_user);

CREATE POLICY "Users can delete own sessions"
ON public.usuario_sessoes
FOR DELETE
USING (username = current_user);

-- ========================================
-- CRIAR ÍNDICES PARA PERFORMANCE
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
-- SELECT * FROM pg_policies WHERE schemaname = 'public';
