/*
   Copyright (C) 2011  Equinor ASA, Norway.

   The file 'well_index.h' is part of ERT - Ensemble based Reservoir Tool.

   ERT is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   ERT is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or
   FITNESS FOR A PARTICULAR PURPOSE.

   See the GNU General Public License at <http://www.gnu.org/licenses/gpl.html>
   for more details.
*/

#ifndef ERT_WELL_INDEX_H
#define ERT_WELL_INDEX_H

#ifdef __cplusplus
extern "C" {
#endif
#include <ert/util/type_macros.hpp>

#include <ert/sched/sched_types.hpp>

typedef struct well_index_struct well_index_type;


void                           well_index_free( well_index_type * well_index );
void                           well_index_add_type( well_index_type * index , sched_kw_type_enum kw_type , sched_history_callback_ftype * func);
sched_history_callback_ftype * well_index_get_callback( const well_index_type * well_index , sched_kw_type_enum kw_type);
const void                   * well_index_get_state( const well_index_type * well_index );


UTIL_IS_INSTANCE_HEADER( well_index );
UTIL_SAFE_CAST_HEADER_CONST( well_index );

#ifdef __cplusplus
}
#endif
#endif
