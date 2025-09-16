FROM docker-registry.ebrains.eu/hdc-services-image/base-image:python-3.10.14-v1 AS base-image

COPY poetry.lock pyproject.toml ./
COPY kg_integration ./kg_integration

RUN poetry install --only main --no-root --no-interaction


FROM base-image AS kg-integration-image

RUN chown -R app:app /app
USER app

CMD ["python3", "-m", "kg_integration"]

FROM base-image AS development-environment

RUN poetry install --no-root --no-interaction


FROM development-environment AS alembic-image

ENV ALEMBIC_CONFIG=migrations/alembic.ini

COPY migrations ./migrations

RUN chown -R app:app /app
USER app

ENTRYPOINT ["python3", "-m", "alembic"]

CMD ["upgrade", "head"]
