"""Debug NL2SQL pipeline step by step."""
import asyncio, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT, "backend"))

from app.nl2sql.pipeline import NL2SQLPipeline, _PROJECT_ROOT

async def main():
    pipeline = NL2SQLPipeline()

    question = "how many vessels are arriving tonight"
    domain = pipeline._detect_domain(question)
    print(f"Domain: {domain}")

    db_path = str(_PROJECT_ROOT / "data" / "sqlite" / f"{domain}.db")
    print(f"DB: {db_path}")

    # Step 1: Extract schema
    print("\n--- Schema ---")
    schema = await pipeline.schema_extractor.extract(db_path, domain)
    for t in schema.tables:
        print(f"  {t['table_name']}: {t['table_desc']} ({len(t['columns'])} cols)")
    print(f"  Prompt text size: {len(schema.to_prompt_text())} chars")

    # Step 2: Generate SQL
    print("\n--- SQL Gen ---")
    sql = await pipeline.sql_generator.generate(question, schema, None, None)
    print(f"  SQL: {sql}")

    # Step 3: Validate
    print("\n--- Validation ---")
    validation = await pipeline.sql_validator.explain_validate(sql, db_path)
    print(f"  Valid: {validation.is_valid}")
    if validation.errors:
        for e in validation.errors:
            print(f"  Error: {e}")

    # Step 4: Try correction if needed
    if not validation.is_valid:
        print("\n--- Retry with errors ---")
        errors = "; ".join(validation.errors)
        sql2 = await pipeline.sql_generator.generate(question, schema, None, errors)
        print(f"  SQL: {sql2}")
        v2 = await pipeline.sql_validator.explain_validate(sql2, db_path)
        print(f"  Valid: {v2.is_valid}")
        if v2.errors:
            for e in v2.errors:
                print(f"  Error: {e}")

        if not v2.is_valid:
            print("\n--- Retry 3 ---")
            errors2 = "; ".join(v2.errors)
            sql3 = await pipeline.sql_generator.generate(question, schema, None, errors2)
            print(f"  SQL: {sql3}")
            v3 = await pipeline.sql_validator.explain_validate(sql3, db_path)
            print(f"  Valid: {v3.is_valid}")
            if v3.errors:
                for e in v3.errors:
                    print(f"  Error: {e}")

asyncio.run(main())
