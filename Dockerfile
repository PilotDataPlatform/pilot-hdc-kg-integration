FROM docker-registry.ebrains.eu/hdc/base-image:python-3.10.10-v1 AS base-image

COPY poetry.lock pyproject.toml ./
COPY kg_integration ./kg_integration

RUN poetry install --only main --no-root --no-interaction


FROM base-image AS kg-integration-image

CMD ["python3", "-m", "kg_integration"]

FROM base-image AS development-environment

RUN poetry install --no-interaction


FROM development-environment AS alembic-image

ENV ALEMBIC_CONFIG=migrations/alembic.ini

COPY migrations ./migrations

ENTRYPOINT ["python3", "-m", "alembic"]

CMD ["upgrade", "head"]
