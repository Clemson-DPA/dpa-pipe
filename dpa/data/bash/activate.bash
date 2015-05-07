
# ----------------------------------------------------------------------------
# Location specific setup
# ----------------------------------------------------------------------------

# XXX everything in this section should be removed before making the dpa-pipe
# repo available to others. This is CU specific stuff.

# ---- DPA PATH setup

# individual paths. separated so that it's easy to add/remove
DPA_PATHS=(
    /opt/pixar/RenderManProServer-18.0/bin \
    /opt/pixar/RenderManStudio-18.0-maya2014/bin \
    /group/dpa/local/openvdb/bin \
    /group/dpa/local/rat2exr/bin \
    /group/dpa/local/MeshPotato/bin \
)

# join them together
DPA_PATH=$(printf ":%s" "${DPA_PATHS[@]}")
DPA_PATH=${DPA_PATH:1}

# set the base
export PATH=${DPA_PATH}:${PATH}

# ---- DPA PYTHONPATH setup

# XXX These paths look suspect. check on these 

## individual paths. separated so that it's easy to add/remove
DPA_PYTHONPATHS=(
    /group/dpa/lib \
    /opt/pixar/RenderManProServer-18.0/bin \
    /group/dpa/local/openvdb/python/lib/python2.7 \
    /group/dpa/local/MeshPotato \
    /group/dpa/scripts/rusterizer \
    /group/dpa/scripts/rat2exr \
)

# join them together
DPA_PYTHONPATH=$(printf ":%s" "${DPA_PYTHONPATHS[@]}")
DPA_PYTHONPATH=${DPA_PYTHONPATH:1}

# set the base
export PYTHONPATH=${DPA_PYTHONPATH}:${PYTHONPATH}

# ---- DPA LD_LIBRARY_PATH setup

# XXX move old stuff from /group/dpa/lib?

# individual paths. separated so that it's easy to add/remove
DPA_LD_LIBRARY_PATHS=(
    /group/dpa/lib \
    /opt/pixar/RenderManProServer-18.0/lib \
    /group/dpa/local/openvdb/lib \
    /group/dpa/local/MeshPotato/lib \
)

# join them together
DPA_LD_LIBRARY_PATH=$(printf ":%s" "${DPA_LD_LIBRARY_PATHS[@]}")
DPA_LD_LIBRARY_PATH=${DPA_LD_LIBRARY_PATH:1}

# set the base
export LD_LIBRARY_PATH=${DPA_LD_LIBRARY_PATH}:${LD_LIBRARY_PATH}

# ----------------------------------------------------------------------------
# Application specific variables
# ----------------------------------------------------------------------------



# ----------------------------------------------------------------------------
# Prompt:
# ----------------------------------------------------------------------------

export DPA_NO_PIPE_PROMPT=$PS1
export DPA_NO_PTASK_PROMPT=$PS1
export DPA_PTASK_PROMPT='[\A][\h] \$DPA_PTASK_SPEC :\n\$(echo \"import os; print os.path.relpath(os.curdir, '"'"'\$DPA_PTASK_PATH'"'"')\" | python) > '

# ----------------------------------------------------------------------------
# Set the virtualenv:
# ----------------------------------------------------------------------------
if [ -n "${DPA_VIRTUAL_ENV}" ]; then
    source ${DPA_VIRTUAL_ENV}/bin/activate

    # add the env name to the prompts
    ENV_NAME="(`basename \"$DPA_VIRTUAL_ENV\"`)"
    export DPA_NO_PTASK_PROMPT="${ENV_NAME}${DPA_NO_PTASK_PROMPT}"
    export DPA_PTASK_PROMPT="${ENV_NAME}${DPA_PTASK_PROMPT}"
fi

# override the virtualenv prompt
export PS1=${DPA_NO_PTASK_PROMPT}

# ----------------------------------------------------------------------------
# Location specifics:
# ----------------------------------------------------------------------------

export DPA_DATA_SERVER="__DPA_DATA_SERVER__"
export DPA_FILESYSTEM_ROOT="__DPA_FILESYSTEM_ROOT__"
export DPA_LOCATION_CODE="__DPA_LOCATION_CODE__"

export DPA_PROJECTS_ROOT="${DPA_FILESYSTEM_ROOT}/projects"
export DPA_SHARE_LOGS="${DPA_FILESYSTEM_ROOT}/.logs"

# ----------------------------------------------------------------------------
# Path variables:
# ----------------------------------------------------------------------------

if [ -n "$LD_LIBRARY_PATH" ];
then
    export DPA_BASE_LD_LIBRARY_PATH="${LD_LIBRARY_PATH}"
else
    export DPA_BASE_LD_LIBRARY_PATH=""
fi

# ----------------------------------------------------------------------------

if [ -n "$PATH" ];
then
    export DPA_BASE_PATH="${PATH}"
else
    export DPA_BASE_PATH=""
fi

# ----------------------------------------------------------------------------

if [ -n "$PYTHONPATH" ];
then
    export DPA_BASE_PYTHONPATH="${PYTHONPATH}"
else
    export DPA_BASE_PYTHONPATH=""
fi

# ----------------------------------------------------------------------------
# Bash functions used withing the pipeline:
# ----------------------------------------------------------------------------

# XXX bash completion is required. Try to activate it.
if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
    . /etc/bash_completion
fi

# ----------------------------------------------------------------------------

# modified version of the colon stripping method from bash completions
__ltrim_equal_completions ()
{
    if [[ "$1" == *=* && ( ${BASH_VERSINFO[0]} -lt 4 || ( ${BASH_VERSINFO[0]} -ge 4 && "$COMP_WORDBREAKS" == *=* ) ) ]]; then
        local colon_word=${1%${1##*=}};
        local i=${#COMPREPLY[*]};
        while [ $((--i)) -ge 0 ]; do
            COMPREPLY[$i]=${COMPREPLY[$i]#"$colon_word"};
        done;
    fi
}

# ----------------------------------------------------------------------------
# noglob wrapper function. from:
#    http://www.chiark.greenend.org.uk/~sgtatham/aliases.html

noglob_helper() {
    "$@"
    case "$shopts" in
        *noglob*) ;;
        *) set +f ;;
    esac
    unset shopts
}

alias noglob='shopts="$SHELLOPTS"; set -f; noglob_helper'

# ----------------------------------------------------------------------------

# evaluate the output of the dpa env command to set a ptask
_dpaset_func () {

    if [[ $@ == **-h** ]];
    then
        eval "dpa env ptask $@";
    else
        eval "`dpa env ptask $@`";
    fi
}

alias dpaset='noglob _dpaset_func'

# ----------------------------------------------------------------------------

# run this function tab complete ptasks via dpaset
# NOTE: if you decide to use something other than '=' as the spec separator,
# you'll need to modify this.

_dpaset_complete () {
    local cur
    # * requires bash completion to be installed
    #     http://bash-completion.alioth.debian.org/
    _get_comp_words_by_ref -n : cur  # *
    COMPREPLY=()
    local word_to_match="${COMP_WORDS[COMP_CWORD]}"
    local completions="$(dpa complete ptask "$word_to_match")"
    COMPREPLY=( $(compgen -W "$completions" -- "$word_to_match") )
    __ltrim_equal_completions "$cur"
}
complete -o nospace -F _dpaset_complete dpaset

# ----------------------------------------------------------------------------
# dpahome
# ----------------------------------------------------------------------------

dpahome () {

    if [ -n "${DPA_PTASK_PATH}" ]; then
        cd ${DPA_PTASK_PATH}
    fi

}

# ----------------------------------------------------------------------------
# Deactivate:
# ----------------------------------------------------------------------------

pipedown () {

    if [ -z "${DPA_DATA_SERVER}" ] &&
       [ -z "${DPA_LOCATION_CODE}" ]; then
        echo
        echo "*** DPA Pipeline was not active. ***"
        echo
        return 
    fi

    # make sure no ptask is set
    dpaset none

    # if the dpa virtualenv is set, unset it
    if [ -n "${DPA_VIRTUAL_ENV}" ] &&
       [ -n "${VIRTUAL_ENV}" ] &&
       [ "${DPA_VIRTUAL_ENV}" == "${VIRTUAL_ENV}" ];
    then
        deactivate
    fi

    # reset the old prompt
    export PS1="${DPA_NO_PIPE_PROMPT}"

    # revert to the origin path variables
    export LD_LIBRARY_PATH="${DPA_BASE_LD_LIBRARY_PATH}"
    export PATH="${DPA_BASE_PATH}"
    export PYTHONPATH="${DPA_BASE_PYTHONPATH}"

    # unset location variables
    unset DPA_BASE_LD_LIBRARY_PATH
    unset DPA_BASE_PATH
    unset DPA_BASE_PYTHONPATH
    unset DPA_DATA_SERVER
    unset DPA_FILESYSTEM_ROOT
    unset DPA_LOCATION_CODE
    unset DPA_NO_PIPE_PROMPT
    unset DPA_NO_PTASK_PROMPT
    unset DPA_PTASK_PATH
    unset DPA_PTASK_PROMPT
    unset DPA_PTASK_SPEC
    unset DPA_PROJECTS_ROOT
    unset DPA_SHARE_LOGS

    # unalias dpa aliases
    # TODO: remember if/what these were aliased to before
    unalias dpaset 2>/dev/null

    unset -f dpahome

    # take user to their home directory (out of ptask hierarchy)
    cd ~

    echo
    echo "*** DPA Pipeline has been deactivated. ***"
    echo
}

# ----------------------------------------------------------------------------
echo
echo "*** DPA Pipeline has been activated ***"
echo

