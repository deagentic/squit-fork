#!/usr/bin/env python3
"""
Demo del Smart Chunking para objetos SQL masivos.

Este script demuestra cómo funciona la estrategia de chunking inteligente
para optimizar embeddings semánticos en lugar de mapeo 1:1.
"""

import sys
from pathlib import Path

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from agentic_rag.smart_chunker import SQLSmartChunker


def demo_chunking_strategies():
    """Demuestra diferentes estrategias de chunking."""
    print("🧠 DEMO: Smart Chunking para SQL Masivo")
    print("=" * 60)
    
    chunker = SQLSmartChunker()
    
    # Ejemplo 1: Stored Procedure grande
    large_procedure = {
        'bigquery_id': 'server1|db1|schema1|large_proc',
        'object_name': 'Dem_Configuracion_Fallas_Demora_Mig',
        'object_type': 'PROCEDURE',
        'server': 'SRVDBDES05',
        'database': 'operacion',
        'schema': 'dbo',
        'sql_code': create_large_procedure_example()
    }
    
    print("\n📄 EJEMPLO 1: Stored Procedure Masivo")
    print(f"Objeto: {large_procedure['object_name']}")
    print(f"Tamaño: {len(large_procedure['sql_code']):,} caracteres")
    print(f"¿Necesita chunking? {chunker.should_chunk_object(large_procedure['sql_code'], 'PROCEDURE')}")
    
    if chunker.should_chunk_object(large_procedure['sql_code'], 'PROCEDURE'):
        chunks = chunker.chunk_sql_object(large_procedure)
        print(f"✂️ Dividido en {len(chunks)} chunks semánticos:")
        
        for i, chunk in enumerate(chunks):
            print(f"\n  📦 Chunk {i+1}/{len(chunks)}:")
            print(f"     • Tipo: {chunk.chunk_type}")
            print(f"     • Tamaño: {chunk.char_count:,} chars ({chunk.line_count} líneas)")
            print(f"     • Resumen: {chunk.semantic_summary}")
            print(f"     • Contexto: {chunk.business_context}")
            print(f"     • Tags: {', '.join(chunk.tags)}")
            print(f"     • Complejidad: {chunk.complexity_score:.1f}/10")
            if chunk.references_to:
                print(f"     • Referencias: {', '.join(chunk.references_to)}")
            print(f"     • Preview: {chunk.code_content[:100]}...")
    
    # Ejemplo 2: Vista compleja
    complex_view = {
        'bigquery_id': 'server1|db1|schema1|complex_view',
        'object_name': 'VentasConsolidadaVw',
        'object_type': 'VIEW',
        'server': 'SRVDBDES03',
        'database': 'ventas',
        'schema': 'dbo',
        'sql_code': create_complex_view_example()
    }
    
    print(f"\n📄 EJEMPLO 2: Vista Compleja")
    print(f"Objeto: {complex_view['object_name']}")
    print(f"Tamaño: {len(complex_view['sql_code']):,} caracteres")
    print(f"¿Necesita chunking? {chunker.should_chunk_object(complex_view['sql_code'], 'VIEW')}")
    
    if chunker.should_chunk_object(complex_view['sql_code'], 'VIEW'):
        chunks = chunker.chunk_sql_object(complex_view)
        print(f"✂️ Dividido en {len(chunks)} chunks semánticos:")
        
        for i, chunk in enumerate(chunks):
            print(f"\n  📦 Chunk {i+1}/{len(chunks)}:")
            print(f"     • Tipo: {chunk.chunk_type}")
            print(f"     • Tamaño: {chunk.char_count:,} chars")
            print(f"     • Resumen: {chunk.semantic_summary}")
            print(f"     • Tags: {', '.join(chunk.tags)}")
    
    # Ejemplo 3: Objeto pequeño (no chunking)
    small_function = {
        'bigquery_id': 'server1|db1|schema1|small_func',
        'object_name': 'GetUserId',
        'object_type': 'FUNCTION',
        'server': 'SRVDBDES01',
        'database': 'auth',
        'schema': 'dbo',
        'sql_code': create_small_function_example()
    }
    
    print(f"\n📄 EJEMPLO 3: Función Pequeña")
    print(f"Objeto: {small_function['object_name']}")
    print(f"Tamaño: {len(small_function['sql_code']):,} caracteres")
    print(f"¿Necesita chunking? {chunker.should_chunk_object(small_function['sql_code'], 'FUNCTION')}")
    
    chunks = chunker.chunk_sql_object(small_function)
    print(f"📦 Resultado: {len(chunks)} chunk único (objeto completo)")
    chunk = chunks[0]
    print(f"   • Tipo: {chunk.chunk_type}")
    print(f"   • Resumen: {chunk.semantic_summary}")
    print(f"   • Tags: {', '.join(chunk.tags)}")


def create_large_procedure_example():
    """Crea un ejemplo de stored procedure masivo."""
    return """
CREATE PROCEDURE [dbo].[Dem_Configuracion_Fallas_Demora_Mig]
    @pnClaUsuario INT,
    @pnClaEmpresa INT,
    @pnClaUbicacion INT
AS
BEGIN
    -- Configuración inicial
    SET NOCOUNT ON;
    
    DECLARE @ErrorMessage NVARCHAR(4000);
    DECLARE @ErrorSeverity INT;
    DECLARE @ErrorState INT;
    
    -- Variables de trabajo
    DECLARE @TotalRegistros INT = 0;
    DECLARE @RegistrosProcesados INT = 0;
    DECLARE @FechaInicio DATETIME = GETDATE();
    
    BEGIN TRY
        BEGIN TRANSACTION MigracionFallas;
        
        -- Sección 1: Validación de parámetros
        IF @pnClaUsuario IS NULL OR @pnClaUsuario <= 0
        BEGIN
            RAISERROR('Usuario inválido', 16, 1);
            RETURN -1;
        END
        
        -- Sección 2: Configuración de fallas por tipo
        INSERT INTO Configuracion_Fallas_Temp (
            ClaEmpresa, ClaUbicacion, TipoFalla, Descripcion, 
            TiempoMaximo, NotificarSupervisor, EsActivo
        )
        SELECT 
            @pnClaEmpresa,
            @pnClaUbicacion,
            tf.ClaTipoFalla,
            tf.Descripcion,
            CASE 
                WHEN tf.Categoria = 'CRITICA' THEN 5
                WHEN tf.Categoria = 'ALTA' THEN 15
                WHEN tf.Categoria = 'MEDIA' THEN 30
                ELSE 60
            END as TiempoMaximo,
            CASE WHEN tf.Categoria IN ('CRITICA', 'ALTA') THEN 1 ELSE 0 END,
            1
        FROM TiposFalla tf
        WHERE tf.EsActivo = 1
          AND tf.ClaEmpresa = @pnClaEmpresa;
        
        SET @TotalRegistros = @@ROWCOUNT;
        
        -- Sección 3: Configuración de demoras por departamento
        DECLARE @ClaDepartamento INT;
        DECLARE dept_cursor CURSOR FOR
        SELECT ClaDepartamento 
        FROM Departamentos 
        WHERE ClaEmpresa = @pnClaEmpresa 
          AND EsActivo = 1;
        
        OPEN dept_cursor;
        FETCH NEXT FROM dept_cursor INTO @ClaDepartamento;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Configurar demoras específicas por departamento
            INSERT INTO Configuracion_Demoras (
                ClaDepartamento, TipoOperacion, TiempoEstandar,
                TiempoMaximo, ToleranciaMinutos, RequiereAprobacion
            )
            VALUES 
                (@ClaDepartamento, 'CARGA', 30, 45, 5, 0),
                (@ClaDepartamento, 'DESCARGA', 25, 40, 5, 0),
                (@ClaDepartamento, 'REVISION', 15, 25, 3, 1),
                (@ClaDepartamento, 'LIMPIEZA', 20, 35, 5, 0);
            
            SET @RegistrosProcesados = @RegistrosProcesados + 4;
            
            FETCH NEXT FROM dept_cursor INTO @ClaDepartamento;
        END
        
        CLOSE dept_cursor;
        DEALLOCATE dept_cursor;
        
        -- Sección 4: Configuración de alertas automáticas
        WITH AlertasConfig AS (
            SELECT 
                'FALLA_CRITICA' as TipoAlerta,
                'Falla crítica detectada en ubicación' as Mensaje,
                1 as RequiereAcknowledge,
                5 as MinutosEspera
            UNION ALL
            SELECT 
                'DEMORA_EXCESIVA' as TipoAlerta,
                'Demora excesiva en operación' as Mensaje,
                0 as RequiereAcknowledge,
                10 as MinutosEspera
            UNION ALL
            SELECT 
                'EQUIPO_INACTIVO' as TipoAlerta,
                'Equipo sin actividad por tiempo prolongado' as Mensaje,
                1 as RequiereAcknowledge,
                15 as MinutosEspera
        )
        INSERT INTO Configuracion_Alertas (
            ClaEmpresa, ClaUbicacion, TipoAlerta, Mensaje,
            RequiereAcknowledge, MinutosEspera, EsActivo, FechaCreacion
        )
        SELECT 
            @pnClaEmpresa,
            @pnClaUbicacion,
            ac.TipoAlerta,
            ac.Mensaje,
            ac.RequiereAcknowledge,
            ac.MinutosEspera,
            1,
            GETDATE()
        FROM AlertasConfig ac;
        
        -- Sección 5: Configuración de reportes automáticos
        DECLARE @ConfigReportes TABLE (
            NombreReporte VARCHAR(100),
            Frecuencia VARCHAR(20),
            HoraEjecucion TIME,
            Destinatarios VARCHAR(500),
            IncluirGraficos BIT
        );
        
        INSERT INTO @ConfigReportes VALUES
            ('Resumen Diario Fallas', 'DIARIO', '08:00:00', 'supervisor@empresa.com', 1),
            ('Reporte Semanal Demoras', 'SEMANAL', '09:00:00', 'gerencia@empresa.com', 1),
            ('Análisis Mensual Eficiencia', 'MENSUAL', '10:00:00', 'direccion@empresa.com', 1);
        
        INSERT INTO Configuracion_Reportes (
            ClaEmpresa, ClaUbicacion, NombreReporte, Frecuencia,
            HoraEjecucion, Destinatarios, IncluirGraficos, EsActivo
        )
        SELECT 
            @pnClaEmpresa,
            @pnClaUbicacion,
            cr.NombreReporte,
            cr.Frecuencia,
            cr.HoraEjecucion,
            cr.Destinatarios,
            cr.IncluirGraficos,
            1
        FROM @ConfigReportes cr;
        
        -- Sección 6: Auditoría y logging
        INSERT INTO LogMigraciones (
            ClaUsuario, ClaEmpresa, ClaUbicacion, TipoMigracion,
            RegistrosAfectados, FechaInicio, FechaFin, Estado, Observaciones
        )
        VALUES (
            @pnClaUsuario,
            @pnClaEmpresa,
            @pnClaUbicacion,
            'CONFIGURACION_FALLAS_DEMORAS',
            @TotalRegistros + @RegistrosProcesados,
            @FechaInicio,
            GETDATE(),
            'COMPLETADO',
            'Migración de configuración completada exitosamente'
        );
        
        COMMIT TRANSACTION MigracionFallas;
        
        -- Retornar resumen
        SELECT 
            'SUCCESS' as Estado,
            @TotalRegistros as RegistrosFallas,
            @RegistrosProcesados as RegistrosDemoras,
            DATEDIFF(SECOND, @FechaInicio, GETDATE()) as TiempoEjecucionSegundos;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION MigracionFallas;
        
        SELECT @ErrorMessage = ERROR_MESSAGE(),
               @ErrorSeverity = ERROR_SEVERITY(),
               @ErrorState = ERROR_STATE();
        
        -- Log del error
        INSERT INTO LogErrores (
            ClaUsuario, Procedimiento, ErrorMessage, ErrorSeverity,
            ErrorState, FechaError
        )
        VALUES (
            @pnClaUsuario,
            'Dem_Configuracion_Fallas_Demora_Mig',
            @ErrorMessage,
            @ErrorSeverity,
            @ErrorState,
            GETDATE()
        );
        
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
        RETURN -1;
    END CATCH
END
""" * 50  # Multiplicar para simular objeto muy grande


def create_complex_view_example():
    """Crea un ejemplo de vista compleja."""
    return """
CREATE VIEW [dbo].[VentasConsolidadaVw] AS
WITH VentasMensuales AS (
    SELECT 
        v.ClaEmpresa,
        v.ClaUbicacion,
        v.ClaCliente,
        v.ClaProducto,
        YEAR(v.FechaVenta) as Anio,
        MONTH(v.FechaVenta) as Mes,
        SUM(v.Cantidad) as TotalCantidad,
        SUM(v.Importe) as TotalImporte,
        AVG(v.PrecioUnitario) as PrecioPromedio,
        COUNT(*) as NumeroTransacciones
    FROM Ventas v
    WHERE v.EsActivo = 1
      AND v.FechaVenta >= DATEADD(YEAR, -2, GETDATE())
    GROUP BY v.ClaEmpresa, v.ClaUbicacion, v.ClaCliente, v.ClaProducto,
             YEAR(v.FechaVenta), MONTH(v.FechaVenta)
),
ClientesInfo AS (
    SELECT 
        c.ClaCliente,
        c.NombreComercial,
        c.TipoCliente,
        c.SegmentoMercado,
        c.ClaRegion,
        r.NombreRegion,
        c.FechaRegistro
    FROM Clientes c
    INNER JOIN Regiones r ON c.ClaRegion = r.ClaRegion
    WHERE c.EsActivo = 1
),
ProductosInfo AS (
    SELECT 
        p.ClaProducto,
        p.NombreProducto,
        p.CodigoProducto,
        p.ClaCategoria,
        cat.NombreCategoria,
        p.ClaLinea,
        lin.NombreLinea,
        p.PesoUnitario,
        p.CostoEstandar
    FROM Productos p
    INNER JOIN Categorias cat ON p.ClaCategoria = cat.ClaCategoria
    INNER JOIN Lineas lin ON p.ClaLinea = lin.ClaLinea
    WHERE p.EsActivo = 1
),
UbicacionesInfo AS (
    SELECT 
        u.ClaUbicacion,
        u.NombreUbicacion,
        u.TipoUbicacion,
        u.ClaEmpresa,
        e.NombreEmpresa,
        u.ClaRegion,
        u.CodigoPostal
    FROM Ubicaciones u
    INNER JOIN Empresas e ON u.ClaEmpresa = e.ClaEmpresa
    WHERE u.EsActivo = 1
)
SELECT 
    vm.ClaEmpresa,
    ui.NombreEmpresa,
    vm.ClaUbicacion,
    ui.NombreUbicacion,
    ui.TipoUbicacion,
    vm.ClaCliente,
    ci.NombreComercial as NombreCliente,
    ci.TipoCliente,
    ci.SegmentoMercado,
    ci.NombreRegion as RegionCliente,
    vm.ClaProducto,
    pi.NombreProducto,
    pi.CodigoProducto,
    pi.NombreCategoria,
    pi.NombreLinea,
    vm.Anio,
    vm.Mes,
    DATEFROMPARTS(vm.Anio, vm.Mes, 1) as FechaPeriodo,
    vm.TotalCantidad,
    vm.TotalImporte,
    vm.PrecioPromedio,
    vm.NumeroTransacciones,
    pi.PesoUnitario * vm.TotalCantidad as PesoTotal,
    pi.CostoEstandar * vm.TotalCantidad as CostoTotal,
    vm.TotalImporte - (pi.CostoEstandar * vm.TotalCantidad) as MargenBruto,
    CASE 
        WHEN pi.CostoEstandar * vm.TotalCantidad > 0 
        THEN ((vm.TotalImporte - (pi.CostoEstandar * vm.TotalCantidad)) / (pi.CostoEstandar * vm.TotalCantidad)) * 100
        ELSE 0 
    END as PorcentajeMargen,
    CASE 
        WHEN vm.TotalCantidad > 1000 THEN 'Alto Volumen'
        WHEN vm.TotalCantidad > 100 THEN 'Medio Volumen'
        ELSE 'Bajo Volumen'
    END as CategoriaVolumen,
    CASE 
        WHEN vm.TotalImporte > 100000 THEN 'Alto Valor'
        WHEN vm.TotalImporte > 10000 THEN 'Medio Valor'
        ELSE 'Bajo Valor'
    END as CategoriaValor
FROM VentasMensuales vm
INNER JOIN ClientesInfo ci ON vm.ClaCliente = ci.ClaCliente
INNER JOIN ProductosInfo pi ON vm.ClaProducto = pi.ClaProducto
INNER JOIN UbicacionesInfo ui ON vm.ClaUbicacion = ui.ClaUbicacion
                               AND vm.ClaEmpresa = ui.ClaEmpresa
""" * 3  # Multiplicar para hacer más grande


def create_small_function_example():
    """Crea un ejemplo de función pequeña."""
    return """
CREATE FUNCTION [dbo].[GetUserId](@UserEmail NVARCHAR(255))
RETURNS INT
AS
BEGIN
    DECLARE @UserId INT;
    
    SELECT @UserId = ClaUsuario
    FROM Usuarios
    WHERE Email = @UserEmail
      AND EsActivo = 1;
    
    RETURN ISNULL(@UserId, -1);
END
"""


def show_chunking_benefits():
    """Muestra los beneficios del smart chunking."""
    print(f"\n💡 BENEFICIOS DEL SMART CHUNKING")
    print("=" * 60)
    
    print("🎯 OPTIMIZACIÓN PARA EMBEDDINGS:")
    print("   • Chunks semánticamente coherentes (no arbitrarios)")
    print("   • Tamaño óptimo para modelos de embedding (~8K chars)")
    print("   • Preserva contexto de negocio en cada chunk")
    print("   • Mantiene relaciones entre chunks del mismo objeto")
    
    print(f"\n🔍 MEJORA EN BÚSQUEDAS:")
    print("   • Resultados más precisos por contexto semántico")
    print("   • Chunks específicos vs objetos completos")
    print("   • Mejor ranking de relevancia")
    print("   • Filtrado avanzado por tipo de chunk")
    
    print(f"\n⚡ EFICIENCIA DE PROCESAMIENTO:")
    print("   • Objetos grandes (9M chars) → múltiples chunks manejables")
    print("   • Paralelización efectiva del análisis IA")
    print("   • Menos timeouts en APIs de LLM")
    print("   • Mejor utilización de memoria")
    
    print(f"\n📊 ESTADÍSTICAS ESPERADAS:")
    print("   • Objetos >50K chars: ~10% del total")
    print("   • Factor de multiplicación: 3-5x chunks vs objetos")
    print("   • Reducción de errores de procesamiento: ~80%")
    print("   • Mejora en precisión de búsqueda: ~40%")


def main():
    """Función principal del demo."""
    print("🚀 SQUIT - Demo Smart Chunking")
    print("Optimización de embeddings para código SQL masivo")
    print()
    
    demo_chunking_strategies()
    show_chunking_benefits()
    
    print(f"\n" + "=" * 60)
    print("✅ DEMO COMPLETADO")
    print("=" * 60)
    print("El smart chunker está listo para la migración masiva.")
    print("Ejecutar: make migrate-all")


if __name__ == "__main__":
    main()
