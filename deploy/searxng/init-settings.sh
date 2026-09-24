#!/bin/sh
# Первый старт: secret_key попадает в volume, в git остаётся только плейсхолдер.
# Повторный старт сохраняет уже записанный hex-ключ и заново накладывает шаблон.
set -eu

TEMPLATE="${SEARXNG_SETTINGS_TEMPLATE:-/usr/local/share/tool-web-search/settings.yml}"
CONFIG_DIR="${__SEARXNG_CONFIG_PATH:-/etc/searxng}"
TARGET="${SEARXNG_SETTINGS_TARGET:-$CONFIG_DIR/settings.yml}"
PLACEHOLDER="${SEARXNG_SECRET_PLACEHOLDER:-__SEARXNG_SECRET_KEY__}"
NEXT="${SEARXNG_NEXT_ENTRYPOINT:-/usr/local/searxng/entrypoint.sh}"

gen_key() {
    if [ -x /usr/local/searxng/.venv/bin/python ]; then
        /usr/local/searxng/.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))'
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 -c 'import secrets; print(secrets.token_hex(32))'
        return
    fi
    if command -v od >/dev/null 2>&1; then
        od -An -N32 -tx1 /dev/urandom | tr -d ' \n'
        return
    fi
    echo "нечем сгенерировать secret_key" >&2
    exit 1
}

extract_key() {
    sed -n 's/^[[:space:]]*secret_key:[[:space:]]*"\([^"]*\)".*/\1/p' "$1" | head -n 1
}

is_stable_key() {
    printf '%s' "$1" | grep -Eq '^[0-9a-f]{64}$'
}

if [ ! -f "$TEMPLATE" ]; then
    echo "нет шаблона настроек: $TEMPLATE" >&2
    exit 1
fi

if ! grep -q "$PLACEHOLDER" "$TEMPLATE"; then
    echo "в шаблоне нет плейсхолдера $PLACEHOLDER" >&2
    exit 1
fi

key=""
if [ -f "$TARGET" ]; then
    key=$(extract_key "$TARGET" || true)
fi

if ! is_stable_key "$key"; then
    key=$(gen_key)
fi

if ! is_stable_key "$key"; then
    echo "secret_key получился не hex" >&2
    exit 1
fi

mkdir -p "$(dirname "$TARGET")"
tmp="${TARGET}.tmp.$$"
sed "s/${PLACEHOLDER}/${key}/g" "$TEMPLATE" > "$tmp"
if grep -q "$PLACEHOLDER" "$tmp"; then
    rm -f "$tmp"
    echo "плейсхолдер остался в настройках" >&2
    exit 1
fi
mv "$tmp" "$TARGET"

if [ "${SEARXNG_INIT_ONLY:-0}" = "1" ]; then
    exit 0
fi

if [ ! -f "$NEXT" ]; then
    echo "нет entrypoint SearXNG: $NEXT" >&2
    exit 1
fi

exec "$NEXT" "$@"
