#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Visual Replication Skill - Installer
#
# Usage:
#   # 方式一：克隆后本地运行
#   git clone https://github.com/ChenZGguo/visual-replication-skill.git
#   cd visual-replication-skill
#   ./install.sh                  # 全局安装（自动检测平台）
#   ./install.sh init             # 在当前项目初始化
#   ./install.sh all              # 全局安装 + 项目初始化
#
#   # 方式二：curl 一键安装（仅全局）
#   curl -fsSL https://raw.githubusercontent.com/ChenZGguo/visual-replication-skill/main/install.sh | bash
#
#   # 指定平台
#   ./install.sh global --platform codewiz
#   ./install.sh init --platform codex
#
# Platforms:
#   codewiz   -> ~/.config/codewiz/skills/visual-replication
#   codex     -> ~/.codex/skills/visual-replication + .codex/hooks.json
#   claude    -> plugin install
#   cursor    -> 无全局安装，仅项目级 .cursorrules
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
ok()    { printf "${GREEN}[OK]${NC}   %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
error() { printf "${RED}[ERROR]${NC} %s\n" "$1" >&2; }
step()  { printf "\n${CYAN}▸ %s${NC}\n" "$1"; }

GITHUB_REPO="https://github.com/ChenZGguo/visual-replication-skill.git"
REPO_NAME="visual-replication-skill"

SKILL_FILES=(
  "SKILL.md"
  "config.json"
  "scripts"
  "hooks"
  "subagents"
  "references"
  "AGENTS.md"
  "LICENSE"
)

PROJECT_FILES_ALL=(
  "AGENTS.md"
  "config.json"
  "scripts"
  "hooks"
)

PROJECT_FILES_CODEX=(
  ".codex/hooks.json"
)

PROJECT_FILES_CURSOR=(
  ".cursorrules"
)

PLATFORM_PATHS=(
  "codewiz:$HOME/.config/codewiz/skills/visual-replication"
  "codex:$HOME/.codex/skills/visual-replication"
)

# ============================================================
# 工具函数
# ============================================================

detect_platform() {
  if [[ -d "$HOME/.config/codewiz" ]] || [[ -n "${CODEWIZ_HOME:-}" ]]; then
    echo "codewiz"
  elif [[ -d "$HOME/.codex" ]]; then
    echo "codex"
  elif command -v claude &>/dev/null; then
    echo "claude"
  elif [[ -d "$HOME/.cursor" ]] || [[ -f "$HOME/.cursorconfig" ]]; then
    echo "cursor"
  else
    echo "codewiz"
  fi
}

resolve_platform() {
  local platform=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --platform)
        if [[ $# -lt 2 || "${2:-}" == --* ]]; then
          error "--platform 需要指定值: codewiz | codex | claude | cursor"
          exit 2
        fi
        platform="$2"
        shift 2
        ;;
      *)
        shift
        ;;
    esac
  done
  if [[ -z "$platform" ]]; then
    platform=$(detect_platform)
    info "自动检测到平台: ${platform}"
  fi
  echo "$platform"
}

get_skill_dir() {
  local platform="$1"
  for entry in "${PLATFORM_PATHS[@]}"; do
    local name="${entry%%:*}"
    local path="${entry#*:}"
    if [[ "$name" == "$platform" ]]; then
      echo "$path"
      return 0
    fi
  done
  return 1
}

get_script_dir() {
  local source="${BASH_SOURCE[0]}"
  local dir
  dir="$(cd "$(dirname "$source")" && pwd)"
  echo "$dir"
}

is_curl_install() {
  [[ ! -f "$1/install.sh" ]]
}

copy_with_backup() {
  local source="$1"
  local target="$2"
  local label="$3"

  if [[ -e "$target" ]]; then
    local backup="${target}.bak.$(date +%Y%m%d%H%M%S)"
    mv "$target" "$backup"
    warn "已备份现有 ${label}: ${backup}"
  fi

  if [[ -d "$source" ]]; then
    cp -R "$source" "$target"
  else
    cp "$source" "$target"
  fi
  ok "已复制: ${label}"
}

download_repo() {
  local tmp_dir
  tmp_dir=$(mktemp -d)
  info "下载仓库到临时目录: ${tmp_dir}"
  if ! git clone --depth 1 "$GITHUB_REPO" "$tmp_dir/$REPO_NAME" 2>/dev/null; then
    error "下载失败，请检查网络或仓库地址: $GITHUB_REPO"
    rm -rf "$tmp_dir"
    return 1
  fi
  echo "$tmp_dir/$REPO_NAME"
}

check_dependencies() {
  step "检查依赖"

  local missing=()

  if ! command -v node &>/dev/null; then
    missing+=("node (Node.js)")
  else
    ok "Node.js: $(node --version)"
  fi

  if ! command -v npx &>/dev/null; then
    missing+=("npx")
  else
    ok "npx 可用"
  fi

  if ! command -v python3 &>/dev/null; then
    missing+=("python3")
  else
    ok "Python: $(python3 --version)"
  fi

  if ! python3 -c "import PIL" &>/dev/null; then
    missing+=("pillow (pip install pillow)")
  else
    ok "Pillow 已安装"
  fi

  if ! python3 -c "import cv2" &>/dev/null; then
    warn "opencv-python 未安装（视频对比功能需要）: pip install opencv-python numpy"
  else
    ok "OpenCV 已安装"
  fi

  if ! npx playwright --version &>/dev/null 2>&1; then
    warn "Playwright 未安装，首次使用时会自动下载"
  else
    ok "Playwright 可用"
  fi

  if [[ ${#missing[@]} -gt 0 ]]; then
    warn "缺少以下依赖:"
    for dep in "${missing[@]}"; do
      printf "  - %s\n" "$dep"
    done
    return 1
  fi
  return 0
}

# ============================================================
# 全局安装
# ============================================================

install_global() {
  local platform
  platform=$(resolve_platform "$@")

  step "全局安装 (平台: ${platform})"

  local script_dir
  script_dir=$(get_script_dir)

  local source_dir
  if is_curl_install "$script_dir"; then
    source_dir=$(download_repo) || return 1
  else
    source_dir="$script_dir"
  fi

  case "$platform" in
    codewiz|codex)
      local skill_dir
      skill_dir=$(get_skill_dir "$platform") || {
        error "不支持的平台: $platform"
        return 1
      }

      info "安装目录: ${skill_dir}"

      if [[ -d "$skill_dir" ]]; then
        local backup_dir="${skill_dir}.bak.$(date +%Y%m%d%H%M%S)"
        warn "目录已存在，将备份后覆盖: ${backup_dir}"
        mv "$skill_dir" "$backup_dir"
      fi

      mkdir -p "$skill_dir"

      for file in "${SKILL_FILES[@]}"; do
        if [[ -e "$source_dir/$file" ]]; then
          cp -R "$source_dir/$file" "$skill_dir/"
        fi
      done

      ok "Skill 已安装到: ${skill_dir}"
      ok "Agent 可通过 SKILL.md 描述自动触发"
      ;;

    claude)
      warn "Claude Code 使用插件系统，请手动执行:"
      printf "  /plugin install %s\n" "$source_dir"
      ;;

    cursor)
      warn "Cursor 无全局 skill 机制，请在每个项目中运行:"
      printf "  ./install.sh init --platform cursor\n"
      ;;

    *)
      error "未知平台: $platform"
      return 1
      ;;
  esac

  check_dependencies || true

  printf "\n${GREEN}全局安装完成。${NC}\n\n"

  printf "下一步：在需要视觉复刻的项目中初始化:\n\n"
  printf "  bash %s/install.sh init --platform %s\n\n" "${skill_dir:-<skill_dir>}" "$platform"
  printf "或手动复制 AGENTS.md、config.json、scripts/、hooks/ 到项目根目录。\n"
}

# ============================================================
# 项目初始化
# ============================================================

install_init() {
  local platform
  platform=$(resolve_platform "$@")

  step "项目初始化 (平台: ${platform})"

  local project_root
  project_root="$(pwd)"

  local script_dir
  script_dir=$(get_script_dir)

  local source_dir="$script_dir"

  info "项目根目录: ${project_root}"

  for file in "${PROJECT_FILES_ALL[@]}"; do
    if [[ -e "$source_dir/$file" ]]; then
      copy_with_backup "$source_dir/$file" "$project_root/$file" "$file"
    fi
  done

  case "$platform" in
    codex)
      for file in "${PROJECT_FILES_CODEX[@]}"; do
        local target="$project_root/$file"
        mkdir -p "$(dirname "$target")"
        if [[ -e "$source_dir/$file" ]]; then
          copy_with_backup "$source_dir/$file" "$target" "$file"
        fi
      done
      ;;

    cursor)
      for file in "${PROJECT_FILES_CURSOR[@]}"; do
        if [[ -e "$source_dir/$file" ]]; then
          copy_with_backup "$source_dir/$file" "$project_root/$file" "$file"
        fi
      done
      ;;

    codewiz|claude)
      ok "平台 ${platform} 所需项目级资源已就绪"
      ;;
  esac

  if [[ ! -d "$project_root/references" ]]; then
    mkdir -p "$project_root/references"
    ok "已创建: references/  (放入参考截图或视频)"
  else
    ok "references/ 已存在"
  fi

  if [[ ! -d "$project_root/artifacts" ]]; then
    mkdir -p "$project_root/artifacts"
    ok "已创建: artifacts/  (验证产物输出目录)"
  fi

  printf "\n${GREEN}项目初始化完成。${NC}\n\n"

  printf "使用方法:\n"
  printf "  1. 将参考截图/视频放入 references/ 目录\n"
  printf "  2. 启动你的项目 (如 localhost:3000)\n"
  printf "  3. 告诉 Agent: \"复刻 references/xxx.png 的界面\"\n"
  printf "  4. Agent 会自动截图、对比、修复差异\n\n"
  printf "验证命令:\n"
  printf "  npx tsx scripts/capture-page.ts --url http://localhost:3000 --output artifacts/actual.png\n"
  printf "  python3 scripts/compare-images.py --reference references/reference.png --actual artifacts/actual.png --output-dir artifacts/diff --report artifacts/visual-report.json\n"
}

# ============================================================
# 全部安装
# ============================================================

install_all() {
  install_global "$@"
  echo ""
  install_init "$@"
}

# ============================================================
# 卸载
# ============================================================

uninstall() {
  local platform
  platform=$(resolve_platform "$@")

  step "卸载 (平台: ${platform})"

  case "$platform" in
    codewiz|codex)
      local skill_dir
      skill_dir=$(get_skill_dir "$platform") || return 1
      if [[ -d "$skill_dir" ]]; then
        rm -rf "$skill_dir"
        ok "已删除: ${skill_dir}"
      else
        warn "目录不存在: ${skill_dir}"
      fi
      ;;
    *)
      warn "平台 ${platform} 无全局安装，无需卸载"
      ;;
  esac

  warn "项目级文件 (AGENTS.md, .codex/hooks.json, .cursorrules) 需手动删除"
}

# ============================================================
# 主入口
# ============================================================

show_help() {
  cat <<'EOF'
Visual Replication Skill Installer

用法:
  ./install.sh [命令] [选项]

命令:
  global      全局安装 skill（Agent 自动调用）
  init        在当前项目初始化（强制验证 Hook + 项目指令）
  all         全局安装 + 项目初始化
  uninstall   卸载全局 skill
  doctor      检查依赖和安装状态
  help        显示帮助

选项:
  --platform <name>   指定平台: codewiz | codex | claude | cursor
                      不指定则自动检测

示例:
  ./install.sh                          # 全局安装（自动检测平台）
  ./install.sh init                     # 初始化当前项目
  ./install.sh init --platform codex    # 初始化 Codex 项目
  curl -fsSL URL/install.sh | bash      # curl 一键全局安装
EOF
}

show_doctor() {
  step "环境诊断"

  printf "\n${CYAN}平台检测:${NC}\n"
  local detected
  detected=$(detect_platform)
  printf "  检测到: %s\n" "$detected"

  printf "\n${CYAN}全局 Skill 安装:${NC}\n"
  for entry in "${PLATFORM_PATHS[@]}"; do
    local name="${entry%%:*}"
    local path="${entry#*:}"
    if [[ -d "$path" ]]; then
      ok "$name: $path"
    else
      printf "  %s: 未安装 (%s)\n" "$name" "$path"
    fi
  done

  printf "\n${CYAN}项目级文件:${NC}\n"
  for f in "AGENTS.md" "config.json" "scripts" "hooks" ".codex/hooks.json" ".cursorrules" "references" "artifacts"; do
    if [[ -e "$f" ]]; then
      ok "$f"
    else
      printf "  %s: 不存在\n" "$f"
    fi
  done

  check_dependencies || true
}

main() {
  local command="${1:-global}"

  case "$command" in
    global)     shift 2>/dev/null || true; install_global "$@" ;;
    init)       shift 2>/dev/null || true; install_init "$@" ;;
    all)        shift 2>/dev/null || true; install_all "$@" ;;
    uninstall)  shift 2>/dev/null || true; uninstall "$@" ;;
    doctor|status) show_doctor ;;
    help|--help|-h) show_help ;;
    *)
      error "未知命令: $command"
      show_help
      exit 1
      ;;
  esac
}

main "$@"
