# Guía de Actualización del Frontend - Gestión de Horarios Médicos

## Resumen de Cambios en el Backend

El sistema de horarios médicos ha sido actualizado para soportar **dos turnos por día** (mañana y tarde) con cupos independientes para cada turno.

### Cambios Principales:
1. **Horarios fijos por turno:**
   - **Mañana:** 07:30 - 13:30
   - **Tarde:** 13:30 - 19:30

2. **Cupos independientes:** Cada turno puede tener diferente cantidad de cupos (ej: 5 mañana, 7 tarde)

3. **Gestión mensual:** Los horarios se gestionan por mes completo

---

## Nuevos Endpoints de la API

### 1. Crear Horarios Mensuales
```
POST /api/horarios/mensual
```

**Request Body:**
```json
{
    "medico_id": 1,
    "area_id": 1,
    "mes": "2025-01",
    "dias_seleccionados": ["2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07", "2025-01-08"],
    "turnos": {
        "manana": {
            "activo": true,
            "cupos": 7
        },
        "tarde": {
            "activo": true,
            "cupos": 7
        }
    }
}
```

**Notas:**
- `dias_seleccionados`: Array de fechas específicas en formato YYYY-MM-DD
- Las fechas deben pertenecer al mes indicado en el campo `mes`
- Al menos un turno debe estar activo
- Si un horario ya existe para esa fecha/turno, se actualiza
- El endpoint valida que las fechas sean del mes correcto

**Response (201):**
```json
{
    "message": "Horarios procesados correctamente",
    "creados": 20,
    "actualizados": 0,
    "total_procesados": 20,
    "advertencias": []  // Solo presente si hubo errores parciales
}
```

### 2. Obtener Horarios
```
GET /api/horarios/
```

**Query Parameters:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `medico_id` | int | Filtrar por médico |
| `area_id` | int | Filtrar por área |
| `mes` | string | Filtrar por mes (YYYY-MM) |
| `fecha` | string | Filtrar por fecha (YYYY-MM-DD) |
| `turno` | string | Filtrar por turno ('M' o 'T') |

**Response:**
```json
[
    {
        "id": 1,
        "medico_id": 1,
        "area_id": 1,
        "fecha": "2025-01-06",
        "dia_semana": 0,
        "turno": "M",
        "turno_nombre": "Mañana",
        "hora_inicio": "07:30:00",
        "hora_fin": "13:30:00",
        "cupos": 5,
        "medico_nombre": "Dr. Juan Pérez",
        "area_nombre": "Medicina General"
    }
]
```

### 3. Obtener Resumen por Mes (para Calendario)
```
GET /api/horarios/resumen?medico_id=1&mes=2025-01
```

**Response:**
```json
{
    "medico_id": 1,
    "mes": "2025-01",
    "dias": [
        {
            "fecha": "2025-01-06",
            "dia_semana": 0,
            "turnos": {
                "M": {
                    "id": 1,
                    "turno": "M",
                    "turno_nombre": "Mañana",
                    "hora_inicio": "07:30:00",
                    "hora_fin": "13:30:00",
                    "cupos": 5,
                    "area_id": 1,
                    "area_nombre": "Medicina General"
                },
                "T": {
                    "id": 2,
                    "turno": "T",
                    "turno_nombre": "Tarde",
                    "hora_inicio": "13:30:00",
                    "hora_fin": "19:30:00",
                    "cupos": 7,
                    "area_id": 1,
                    "area_nombre": "Medicina General"
                }
            }
        }
    ]
}
```

### 4. Eliminar Horarios del Mes
```
DELETE /api/horarios/mensual?medico_id=1&mes=2025-01&turno=M
```

**Query Parameters:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `medico_id` | int | (Requerido) ID del médico |
| `mes` | string | (Requerido) Mes (YYYY-MM) |
| `turno` | string | (Opcional) 'M' o 'T' para eliminar solo un turno |

---

## Cambios Requeridos en el Frontend

### 1. Actualizar `horarioService.ts`

```typescript
import api from './api'

export interface Turno {
    id?: number
    turno: 'M' | 'T'
    turno_nombre: string
    hora_inicio: string
    hora_fin: string
    cupos: number
    area_id?: number
    area_nombre?: string
}

export interface HorarioDia {
    fecha: string
    dia_semana: number
    turnos: {
        M?: Turno
        T?: Turno
    }
}

export interface Horario {
    id?: number
    medico_id?: number
    area_id?: number
    fecha?: string
    dia_semana: number
    turno: 'M' | 'T'
    turno_nombre?: string
    hora_inicio: string
    hora_fin: string
    cupos: number
    medico_nombre?: string
    area_nombre?: string
}

export interface TurnoConfig {
    activo: boolean
    cupos: number
}

export interface CrearHorariosMensualesPayload {
    medico_id: number
    area_id: number
    mes: string  // YYYY-MM
    dias_seleccionados: string[]  // Array de fechas "YYYY-MM-DD"
    turnos: {
        manana: TurnoConfig
        tarde: TurnoConfig
    }
}

export interface ResumenMes {
    medico_id: number
    mes: string
    dias: HorarioDia[]
}

const horarioService = {
    // Crear horarios para todo el mes
    crearHorariosMensuales(payload: CrearHorariosMensualesPayload) {
        return api.post('/horarios/mensual', payload)
    },

    // Obtener horarios con filtros
    getHorarios(params?: {
        medico_id?: number | null
        area_id?: number | null
        mes?: string
        fecha?: string
        turno?: 'M' | 'T'
    }) {
        return api.get<Horario[]>('/horarios/', { params })
    },

    // Obtener resumen del mes para calendario
    getResumenMes(medico_id: number, mes: string) {
        return api.get<ResumenMes>('/horarios/resumen', {
            params: { medico_id, mes }
        })
    },

    // Eliminar un horario específico
    eliminarHorario(id: number) {
        return api.delete(`/horarios/${id}`)
    },

    // Eliminar horarios de un mes
    eliminarHorariosMes(medico_id: number, mes: string, turno?: 'M' | 'T') {
        return api.delete('/horarios/mensual', {
            params: { medico_id, mes, turno }
        })
    },

    // Crear horario individual (legacy compatible)
    crearHorario(data: any) {
        return api.post('/horarios/', data)
    }
}

export default horarioService
```

### 2. Actualizar el Formulario del Modal en `AdminHorarios.vue`

Reemplazar la sección de "Horarios y Cupos" en el modal por los dos turnos:

```vue
<template>
    <!-- ... resto del template ... -->

    <!-- Modal Configurar Horario Mensual -->
    <div v-if="modalVisible" class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 px-4">
        <div class="bg-white rounded-2xl max-w-2xl w-full shadow-2xl">
            <!-- Header del modal -->
            <div class="bg-gradient-to-r from-teal-600 to-teal-700 px-6 py-4 text-white">
                <div class="flex justify-between items-center">
                    <div>
                        <h3 class="text-xl font-bold">Configurar Horario Mensual</h3>
                        <p class="text-teal-100 text-sm mt-1">Programa los turnos del médico para el mes</p>
                    </div>
                    <button @click="cerrarModal" class="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center">
                        <i class="pi pi-times"></i>
                    </button>
                </div>
            </div>

            <!-- Contenido del modal -->
            <div class="p-6 overflow-y-auto max-h-[70vh]">
                <form @submit.prevent="guardarHorarioMensual" class="space-y-5">
                    
                    <!-- Médico y Área -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">
                                <i class="pi pi-user mr-1 text-teal-600"></i>
                                Médico <span class="text-red-500">*</span>
                            </label>
                            <select v-model="form.medico_id" required class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500">
                                <option :value="null">Seleccione un médico</option>
                                <option v-for="medico in medicos" :key="medico.id" :value="medico.id">
                                    {{ medico.name }}
                                </option>
                            </select>
                        </div>

                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">
                                <i class="pi pi-building mr-1 text-teal-600"></i>
                                Área <span class="text-red-500">*</span>
                            </label>
                            <select v-model="form.area_id" required class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500">
                                <option :value="null">Seleccione un área</option>
                                <option v-for="area in areas" :key="area.id" :value="area.id">
                                    {{ area.nombre }}
                                </option>
                            </select>
                        </div>
                    </div>

                    <!-- Mes -->
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">
                            <i class="pi pi-calendar mr-1 text-teal-600"></i>
                            Mes <span class="text-red-500">*</span>
                        </label>
                        <input type="month" v-model="form.mes" required 
                            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500" />
                    </div>

                    <!-- Días de la semana -->
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-3">
                            <i class="pi pi-calendar-plus mr-1 text-teal-600"></i>
                            Días de Atención <span class="text-red-500">*</span>
                        </label>
                        <div class="grid grid-cols-4 md:grid-cols-7 gap-2">
                            <label v-for="(dia, index) in diasSemana" :key="index" 
                                :class="[
                                    'flex flex-col items-center p-3 border-2 rounded-xl cursor-pointer transition-all',
                                    form.dias_seleccionados.includes(index)
                                        ? 'bg-teal-50 border-teal-500 text-teal-700'
                                        : 'border-gray-200 hover:border-gray-300 text-gray-600'
                                ]">
                                <input type="checkbox" :value="index" v-model="form.dias_seleccionados" class="sr-only" />
                                <span class="font-bold text-lg">{{ dia }}</span>
                                <i v-if="form.dias_seleccionados.includes(index)" class="pi pi-check-circle text-teal-600 mt-1"></i>
                                <i v-else class="pi pi-circle text-gray-300 mt-1"></i>
                            </label>
                        </div>
                        <div class="flex gap-2 mt-3">
                            <button type="button" @click="seleccionarDiasLaborables" class="text-xs text-teal-600 hover:text-teal-700 font-medium">
                                Lun-Vie
                            </button>
                            <span class="text-gray-300">|</span>
                            <button type="button" @click="seleccionarTodosDias" class="text-xs text-teal-600 hover:text-teal-700 font-medium">
                                Todos
                            </button>
                            <span class="text-gray-300">|</span>
                            <button type="button" @click="form.dias_seleccionados = []" class="text-xs text-gray-500 hover:text-gray-700 font-medium">
                                Ninguno
                            </button>
                        </div>
                    </div>

                    <!-- NUEVA SECCIÓN: Configuración de Turnos -->
                    <div class="space-y-4">
                        <label class="block text-sm font-semibold text-gray-700">
                            <i class="pi pi-clock mr-1 text-teal-600"></i>
                            Configuración de Turnos
                        </label>

                        <!-- Turno Mañana -->
                        <div :class="[
                            'border-2 rounded-xl p-4 transition-all',
                            form.turnos.manana.activo 
                                ? 'border-amber-400 bg-amber-50' 
                                : 'border-gray-200 bg-gray-50'
                        ]">
                            <div class="flex items-center justify-between mb-3">
                                <div class="flex items-center gap-3">
                                    <div class="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                                        <i class="pi pi-sun text-amber-600 text-lg"></i>
                                    </div>
                                    <div>
                                        <h4 class="font-semibold text-gray-800">Turno Mañana</h4>
                                        <p class="text-sm text-gray-500">07:30 - 13:30</p>
                                    </div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" v-model="form.turnos.manana.activo" class="sr-only peer">
                                    <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-amber-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
                                </label>
                            </div>
                            
                            <div v-if="form.turnos.manana.activo" class="flex items-center gap-3">
                                <label class="text-sm text-gray-600">Cupos:</label>
                                <input type="number" v-model.number="form.turnos.manana.cupos" min="1" max="50"
                                    class="w-20 px-3 py-2 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 text-center font-semibold" />
                                <span class="text-sm text-gray-500">citas disponibles</span>
                            </div>
                        </div>

                        <!-- Turno Tarde -->
                        <div :class="[
                            'border-2 rounded-xl p-4 transition-all',
                            form.turnos.tarde.activo 
                                ? 'border-indigo-400 bg-indigo-50' 
                                : 'border-gray-200 bg-gray-50'
                        ]">
                            <div class="flex items-center justify-between mb-3">
                                <div class="flex items-center gap-3">
                                    <div class="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                                        <i class="pi pi-moon text-indigo-600 text-lg"></i>
                                    </div>
                                    <div>
                                        <h4 class="font-semibold text-gray-800">Turno Tarde</h4>
                                        <p class="text-sm text-gray-500">13:30 - 19:30</p>
                                    </div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" v-model="form.turnos.tarde.activo" class="sr-only peer">
                                    <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-500"></div>
                                </label>
                            </div>
                            
                            <div v-if="form.turnos.tarde.activo" class="flex items-center gap-3">
                                <label class="text-sm text-gray-600">Cupos:</label>
                                <input type="number" v-model.number="form.turnos.tarde.cupos" min="1" max="50"
                                    class="w-20 px-3 py-2 border border-indigo-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-center font-semibold" />
                                <span class="text-sm text-gray-500">citas disponibles</span>
                            </div>
                        </div>
                    </div>

                    <!-- Resumen visual -->
                    <div v-if="form.dias_seleccionados.length > 0 && form.mes && (form.turnos.manana.activo || form.turnos.tarde.activo)"
                        class="bg-gradient-to-r from-blue-50 to-teal-50 border border-blue-200 rounded-xl p-4">
                        <h4 class="font-bold text-blue-900 mb-3 flex items-center gap-2">
                            <i class="pi pi-info-circle"></i>
                            Resumen de Configuración
                        </h4>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                                    <i class="pi pi-calendar text-blue-600"></i>
                                </div>
                                <div>
                                    <p class="text-gray-500 text-xs">Días</p>
                                    <p class="font-bold text-blue-800">{{ contarDiasLaborables() }}</p>
                                </div>
                            </div>
                            <div v-if="form.turnos.manana.activo" class="flex items-center gap-2">
                                <div class="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                                    <i class="pi pi-sun text-amber-600"></i>
                                </div>
                                <div>
                                    <p class="text-gray-500 text-xs">Mañana</p>
                                    <p class="font-bold text-amber-800">{{ contarDiasLaborables() * form.turnos.manana.cupos }} cupos</p>
                                </div>
                            </div>
                            <div v-if="form.turnos.tarde.activo" class="flex items-center gap-2">
                                <div class="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                                    <i class="pi pi-moon text-indigo-600"></i>
                                </div>
                                <div>
                                    <p class="text-gray-500 text-xs">Tarde</p>
                                    <p class="font-bold text-indigo-800">{{ contarDiasLaborables() * form.turnos.tarde.cupos }} cupos</p>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 bg-teal-100 rounded-lg flex items-center justify-center">
                                    <i class="pi pi-ticket text-teal-600"></i>
                                </div>
                                <div>
                                    <p class="text-gray-500 text-xs">Total</p>
                                    <p class="font-bold text-teal-800">{{ calcularTotalCupos() }} cupos</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Validación: al menos un turno activo -->
                    <div v-if="!form.turnos.manana.activo && !form.turnos.tarde.activo" 
                        class="bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm flex items-center gap-2">
                        <i class="pi pi-exclamation-triangle"></i>
                        Debe activar al menos un turno (mañana o tarde)
                    </div>

                    <!-- Botones -->
                    <div class="flex gap-3 pt-2">
                        <button type="submit" 
                            :disabled="isLoading || form.dias_seleccionados.length === 0 || (!form.turnos.manana.activo && !form.turnos.tarde.activo)"
                            class="flex-1 bg-teal-600 hover:bg-teal-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-xl transition flex items-center justify-center gap-2">
                            <i v-if="isLoading" class="pi pi-spin pi-spinner"></i>
                            <i v-else class="pi pi-check-circle"></i>
                            {{ isLoading ? 'Guardando...' : 'Crear Horarios' }}
                        </button>
                        <button type="button" @click="cerrarModal"
                            class="px-6 py-3 border-2 border-gray-300 text-gray-600 hover:bg-gray-50 font-semibold rounded-xl transition">
                            Cancelar
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>
```

### 3. Actualizar el Script del Componente

```typescript
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../../services/api'
import horarioService, { type Horario, type HorarioDia } from '../../services/horarioService'

const diasSemana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const diasSemanaCompletos = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

const areas = ref<any[]>([])
const medicos = ref<any[]>([])
const horariosList = ref<Horario[]>([])
const filtroAreaId = ref<number | null>(null)
const filtroMedicoId = ref<number | null>(null)
const filtroMes = ref('')
const filtroTurno = ref<'M' | 'T' | null>(null)  // NUEVO: filtro por turno
const vistaActual = ref<'tabla' | 'tarjetas' | 'calendario'>('tabla')

const modalVisible = ref(false)
const isLoading = ref(false)
const isLoadingList = ref(false)
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')

// NUEVO: Estructura del formulario con turnos
const form = ref({
    medico_id: null as number | null,
    area_id: null as number | null,
    mes: '',
    dias_seleccionados: [] as number[],
    turnos: {
        manana: {
            activo: true,
            cupos: 5
        },
        tarde: {
            activo: true,
            cupos: 7
        }
    }
})

// Calcular total de cupos
const calcularTotalCupos = () => {
    const dias = contarDiasLaborables()
    let total = 0
    if (form.value.turnos.manana.activo) {
        total += dias * form.value.turnos.manana.cupos
    }
    if (form.value.turnos.tarde.activo) {
        total += dias * form.value.turnos.tarde.cupos
    }
    return total
}

// Contar días laborables del mes
const contarDiasLaborables = () => {
    if (!form.value.mes || form.value.dias_seleccionados.length === 0) return 0

    const parts = form.value.mes.split('-').map(Number)
    if (parts.length < 2 || parts[0] === undefined || parts[1] === undefined) return 0
    const year = parts[0]
    const month = parts[1]
    const ultimoDia = new Date(year, month, 0).getDate()
    let contador = 0

    for (let dia = 1; dia <= ultimoDia; dia++) {
        const fecha = new Date(year, month - 1, dia)
        const diaSemana = fecha.getDay() === 0 ? 6 : fecha.getDay() - 1
        if (form.value.dias_seleccionados.includes(diaSemana)) {
            contador++
        }
    }

    return contador
}

// Abrir modal con valores por defecto
const abrirModalHorario = () => {
    modalVisible.value = true
    const hoy = new Date()
    const mesActual = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}`

    form.value = {
        medico_id: null,
        area_id: null,
        mes: mesActual,
        dias_seleccionados: [0, 1, 2, 3, 4],  // Lun-Vie por defecto
        turnos: {
            manana: {
                activo: true,
                cupos: 5
            },
            tarde: {
                activo: true,
                cupos: 7
            }
        }
    }
}

// ACTUALIZADO: Guardar horarios mensuales con nuevo endpoint
const guardarHorarioMensual = async () => {
    if (!form.value.medico_id || !form.value.area_id || form.value.dias_seleccionados.length === 0) return
    if (!form.value.turnos.manana.activo && !form.value.turnos.tarde.activo) return

    isLoading.value = true
    try {
        const payload = {
            medico_id: form.value.medico_id,
            area_id: form.value.area_id,
            mes: form.value.mes,
            dias_seleccionados: form.value.dias_seleccionados,
            turnos: form.value.turnos
        }

        const { data } = await horarioService.crearHorariosMensuales(payload)
        
        mostrarToast(`${data.creados} horarios creados, ${data.actualizados} actualizados`, 'success')
        cerrarModal()
        cargarHorariosFiltrados()
    } catch (error: any) {
        console.error('Error al guardar horarios', error)
        const mensaje = error.response?.data?.error || 'Error al guardar los horarios'
        mostrarToast(mensaje, 'error')
    } finally {
        isLoading.value = false
    }
}

// ACTUALIZADO: Cargar horarios con filtro de turno
const cargarHorariosFiltrados = async () => {
    isLoadingList.value = true
    try {
        const params = {
            area_id: filtroAreaId.value,
            medico_id: filtroMedicoId.value,
            mes: filtroMes.value || undefined,
            turno: filtroTurno.value || undefined
        }
        const { data } = await horarioService.getHorarios(params)
        horariosList.value = data

    } catch (error) {
        console.error('Error al cargar horarios', error)
        horariosList.value = []
    } finally {
        isLoadingList.value = false
    }
}

// Resto de funciones...
const seleccionarDiasLaborables = () => {
    form.value.dias_seleccionados = [0, 1, 2, 3, 4]
}

const seleccionarTodosDias = () => {
    form.value.dias_seleccionados = [0, 1, 2, 3, 4, 5, 6]
}

const cerrarModal = () => {
    modalVisible.value = false
}

const eliminarHorario = async (id: number | undefined) => {
    if (!id) return
    if (!confirm('¿Está seguro de eliminar este horario?')) return

    try {
        await horarioService.eliminarHorario(id)
        mostrarToast('Horario eliminado exitosamente', 'success')
        cargarHorariosFiltrados()
    } catch (error) {
        console.error('Error al eliminar horario', error)
        mostrarToast('Error al eliminar horario', 'error')
    }
}

const mostrarToast = (mensaje: string, tipo: 'success' | 'error' = 'success') => {
    toastMessage.value = mensaje
    toastType.value = tipo
    showToast.value = true
    setTimeout(() => {
        showToast.value = false
    }, 3000)
}

// Helpers para la tabla
const getTurnoBadgeClass = (turno: string) => {
    return turno === 'M' 
        ? 'bg-amber-100 text-amber-800' 
        : 'bg-indigo-100 text-indigo-800'
}

onMounted(() => {
    fetchAreas()
    fetchMedicos()
    const hoy = new Date()
    filtroMes.value = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}`
    cargarHorariosFiltrados()
})
</script>
```

### 4. Actualizar la Tabla de Horarios

Añadir columna de turno en la tabla:

```vue
<thead class="bg-gray-50 border-b border-gray-200">
    <tr>
        <th class="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">
            <div class="flex items-center gap-2">
                <i class="pi pi-user text-teal-500"></i>
                Médico
            </div>
        </th>
        <th class="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">
            <div class="flex items-center gap-2">
                <i class="pi pi-building text-teal-500"></i>
                Área
            </div>
        </th>
        <th class="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">
            <div class="flex items-center gap-2">
                <i class="pi pi-calendar text-teal-500"></i>
                Fecha
            </div>
        </th>
        <!-- NUEVA COLUMNA -->
        <th class="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">
            <div class="flex items-center gap-2">
                <i class="pi pi-clock text-teal-500"></i>
                Turno
            </div>
        </th>
        <th class="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">
            <div class="flex items-center gap-2">
                <i class="pi pi-ticket text-teal-500"></i>
                Cupos
            </div>
        </th>
        <th class="px-6 py-4 text-center text-xs font-semibold text-gray-600 uppercase">
            Acciones
        </th>
    </tr>
</thead>
<tbody class="bg-white divide-y divide-gray-100">
    <tr v-for="horario in horariosList" :key="horario.id" class="hover:bg-gray-50 transition-colors">
        <td class="px-6 py-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-teal-100 text-teal-700 rounded-full flex items-center justify-center font-semibold">
                    {{ getInitials(horario.medico_nombre || '') }}
                </div>
                <span class="font-medium text-gray-900">{{ horario.medico_nombre }}</span>
            </div>
        </td>
        <td class="px-6 py-4">
            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {{ horario.area_nombre }}
            </span>
        </td>
        <td class="px-6 py-4">
            <div class="text-gray-700">
                {{ formatearFecha(horario.fecha) }}
            </div>
            <div class="text-xs text-gray-500">
                {{ diasSemanaCompletos[horario.dia_semana] }}
            </div>
        </td>
        <!-- NUEVA CELDA DE TURNO -->
        <td class="px-6 py-4">
            <div class="flex items-center gap-2">
                <span :class="[
                    'px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1',
                    getTurnoBadgeClass(horario.turno)
                ]">
                    <i :class="horario.turno === 'M' ? 'pi pi-sun' : 'pi pi-moon'" class="text-xs"></i>
                    {{ horario.turno_nombre }}
                </span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
                {{ horario.hora_inicio?.slice(0, 5) }} - {{ horario.hora_fin?.slice(0, 5) }}
            </div>
        </td>
        <td class="px-6 py-4">
            <div class="w-10 h-10 bg-emerald-100 text-emerald-700 rounded-lg flex items-center justify-center font-bold">
                {{ horario.cupos }}
            </div>
        </td>
        <td class="px-6 py-4">
            <div class="flex items-center justify-center gap-2">
                <button @click="eliminarHorario(horario.id)" class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition">
                    <i class="pi pi-trash"></i>
                </button>
            </div>
        </td>
    </tr>
</tbody>
```

### 5. Añadir Filtro por Turno

En la sección de filtros, añadir:

```vue
<div>
    <label class="block text-sm font-medium text-gray-600 mb-2">
        <i class="pi pi-clock mr-1"></i> Turno
    </label>
    <select v-model="filtroTurno" @change="cargarHorariosFiltrados"
        class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500">
        <option :value="null">Todos los turnos</option>
        <option value="M">🌞 Mañana (07:30-13:30)</option>
        <option value="T">🌙 Tarde (13:30-19:30)</option>
    </select>
</div>
```

### 6. Helper para Formatear Fecha

```typescript
const formatearFecha = (fecha: string | undefined) => {
    if (!fecha) return ''
    const date = new Date(fecha + 'T00:00:00')
    return date.toLocaleDateString('es-PE', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric' 
    })
}
```

---

## Resumen de Estadísticas Actualizado

Actualizar el cómputo de `totalCupos` para mostrar desglose por turno:

```typescript
const totalCuposManana = computed(() => {
    return horariosList.value
        .filter(h => h.turno === 'M')
        .reduce((sum, h) => sum + h.cupos, 0)
})

const totalCuposTarde = computed(() => {
    return horariosList.value
        .filter(h => h.turno === 'T')
        .reduce((sum, h) => sum + h.cupos, 0)
})

const totalCupos = computed(() => {
    return totalCuposManana.value + totalCuposTarde.value
})
```

---

## Vista de Calendario Actualizada

Para mostrar ambos turnos en el calendario:

```vue
<div v-for="dia in diasDelMes" :key="dia.fecha" 
    :class="[
        'p-2 rounded-lg border min-h-[100px]',
        dia.esDelMes ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-100',
        (dia.turnos?.M || dia.turnos?.T) ? 'border-teal-400 border-2' : ''
    ]">
    <div v-if="dia.esDelMes">
        <div class="font-bold text-gray-700 mb-2 text-sm">{{ dia.numero }}</div>
        
        <!-- Turno Mañana -->
        <div v-if="dia.turnos?.M" 
            class="text-xs bg-amber-500 text-white px-2 py-1 rounded mb-1 flex items-center gap-1">
            <i class="pi pi-sun text-[10px]"></i>
            <span>{{ dia.turnos.M.cupos }} cupos</span>
        </div>
        
        <!-- Turno Tarde -->
        <div v-if="dia.turnos?.T" 
            class="text-xs bg-indigo-500 text-white px-2 py-1 rounded flex items-center gap-1">
            <i class="pi pi-moon text-[10px]"></i>
            <span>{{ dia.turnos.T.cupos }} cupos</span>
        </div>
        
        <div v-if="!dia.turnos?.M && !dia.turnos?.T" class="text-xs text-gray-400 italic">
            Sin horario
        </div>
    </div>
</div>
```

---

## Notas Importantes

1. **Horarios Fijos:** Los horarios de inicio/fin ya no se configuran manualmente. Son fijos:
   - Mañana: 07:30 - 13:30
   - Tarde: 13:30 - 19:30

2. **Migración:** El backend ya está actualizado. Solo necesitas adaptar el frontend.

3. **Compatibilidad:** Los endpoints legacy siguen funcionando pero devuelven el nuevo formato.

4. **Constraint Único:** No puede haber dos horarios para el mismo médico, fecha y turno.

---

# Guía de Implementación: Descarga de PDF de Citas Confirmadas

Esta guía describe cómo implementar la funcionalidad de descarga de PDF de citas confirmadas para impresión.

## Objetivo

Permitir a los usuarios descargar un PDF con la lista de citas confirmadas filtradas por **fecha** y **área**, ordenadas por fecha de registro (orden de llegada) y numeradas para ser publicadas en la entrada del servicio.

---

## 1. Endpoints Disponibles

### **GET /api/citas/confirmadas**
Retorna JSON con las citas confirmadas.

### **GET /api/citas/confirmadas/pdf**
Retorna un archivo PDF para descarga directa.

**Parámetros (ambos endpoints):**
| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `fecha` | string (YYYY-MM-DD) | ✅ Sí | Fecha de las citas |
| `area_id` | integer | ✅ Sí | ID del área/servicio |

---

## 2. Actualizar `citaService.ts`

Agregar las interfaces y métodos para citas confirmadas y descarga de PDF:

```typescript
// src/services/citaService.ts
import api from './api'

// ============================================
// INTERFACES PARA CITAS CONFIRMADAS
// ============================================

export interface CitaConfirmadaParams {
  fecha: string;       // YYYY-MM-DD
  area_id: number;
}

export interface CitaConfirmadaPaciente {
  id: number;
  nombres: string;
  apellido_paterno: string;
  apellido_materno: string;
  dni: string;
  telefono?: string | null;
}

export interface CitaConfirmadaHorario {
  id: number;
  hora_inicio: string;
  hora_fin: string;
  turno: 'M' | 'T';
  turno_nombre: string;
}

export interface CitaConfirmadaItem {
  numero: number;
  id: number;
  paciente: CitaConfirmadaPaciente | null;
  horario: CitaConfirmadaHorario | null;
  fecha_registro: string | null;
}

export interface CitaConfirmadaResponse {
  success: boolean;
  fecha: string;
  area: {
    id: number;
    nombre: string;
  };
  total: number;
  citas: CitaConfirmadaItem[];
}

// ============================================
// SERVICIO DE CITAS
// ============================================

const citaService = {
  // ... otros métodos existentes ...

  /**
   * Obtener citas confirmadas (respuesta JSON)
   * Útil para vista previa antes de imprimir
   */
  getCitasConfirmadas(params: CitaConfirmadaParams) {
    return api.get<CitaConfirmadaResponse>('/citas/confirmadas', { params });
  },

  /**
   * Descargar PDF de citas confirmadas
   * Retorna un Blob con el archivo PDF
   */
  descargarPDFCitasConfirmadas(params: CitaConfirmadaParams) {
    return api.get('/citas/confirmadas/pdf', {
      params,
      responseType: 'blob'  // ¡Importante! Recibir como blob para archivos
    });
  }
}

export default citaService
```

---

## 3. Crear Componente de Impresión de Citas

Crear un nuevo componente `ImprimirCitas.vue` o integrarlo en `AdminCitas.vue`:

### Opción A: Modal de Impresión (recomendado)

```vue
<!-- src/components/modals/ModalImprimirCitas.vue -->
<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden">
      
      <!-- Header -->
      <div class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 text-white">
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <i class="pi pi-print text-xl"></i>
            </div>
            <div>
              <h3 class="text-xl font-bold">Imprimir Citas Confirmadas</h3>
              <p class="text-blue-100 text-sm">Generar PDF para publicar</p>
            </div>
          </div>
          <button @click="cerrar" class="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center transition">
            <i class="pi pi-times"></i>
          </button>
        </div>
      </div>

      <!-- Contenido -->
      <div class="p-6 space-y-5">
        
        <!-- Selector de Fecha -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">
            <i class="pi pi-calendar mr-1 text-blue-600"></i>
            Fecha de las citas <span class="text-red-500">*</span>
          </label>
          <input 
            type="date" 
            v-model="fecha" 
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
          />
        </div>

        <!-- Selector de Área -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">
            <i class="pi pi-building mr-1 text-blue-600"></i>
            Área / Servicio <span class="text-red-500">*</span>
          </label>
          <select 
            v-model="areaId" 
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
          >
            <option :value="null">Seleccione un área</option>
            <option v-for="area in areas" :key="area.id" :value="area.id">
              {{ area.nombre }}
            </option>
          </select>
        </div>

        <!-- Vista Previa -->
        <div v-if="citasPreview" class="bg-gray-50 rounded-xl p-4 border border-gray-200">
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-semibold text-gray-700">Vista Previa</span>
            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-bold">
              {{ citasPreview.total }} citas
            </span>
          </div>
          
          <div v-if="citasPreview.total === 0" class="text-center py-4 text-gray-500">
            <i class="pi pi-inbox text-3xl mb-2"></i>
            <p class="text-sm">No hay citas confirmadas para esta fecha y área</p>
          </div>
          
          <div v-else class="space-y-2 max-h-40 overflow-y-auto">
            <div 
              v-for="cita in citasPreview.citas.slice(0, 5)" 
              :key="cita.id"
              class="flex items-center gap-3 p-2 bg-white rounded-lg border border-gray-100"
            >
              <span class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                {{ cita.numero }}
              </span>
              <div class="flex-1 min-w-0">
                <p class="font-medium text-gray-800 truncate">
                  {{ cita.paciente?.apellido_paterno }} {{ cita.paciente?.apellido_materno }}, {{ cita.paciente?.nombres }}
                </p>
                <p class="text-xs text-gray-500">DNI: {{ cita.paciente?.dni }}</p>
              </div>
              <span class="text-xs text-gray-400">
                {{ cita.horario?.hora_inicio?.slice(0, 5) }}
              </span>
            </div>
            <p v-if="citasPreview.total > 5" class="text-center text-sm text-gray-500 pt-2">
              ... y {{ citasPreview.total - 5 }} más
            </p>
          </div>
        </div>

        <!-- Mensaje de Error -->
        <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3 text-red-700">
          <i class="pi pi-exclamation-triangle"></i>
          <span class="text-sm">{{ error }}</span>
        </div>

      </div>

      <!-- Footer con Botones -->
      <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
        <button 
          @click="verVistaPrevia"
          :disabled="!fecha || !areaId || loadingPreview"
          class="flex-1 px-4 py-3 border-2 border-blue-600 text-blue-600 font-semibold rounded-xl hover:bg-blue-50 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <i v-if="loadingPreview" class="pi pi-spin pi-spinner"></i>
          <i v-else class="pi pi-eye"></i>
          Vista Previa
        </button>
        <button 
          @click="descargarPDF"
          :disabled="!fecha || !areaId || loadingPDF"
          class="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <i v-if="loadingPDF" class="pi pi-spin pi-spinner"></i>
          <i v-else class="pi pi-download"></i>
          Descargar PDF
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import citaService, { type CitaConfirmadaResponse } from '@/services/citaService'
import areaService from '@/services/areaService'

// Props
const props = defineProps<{
  visible: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'close'): void
}>()

// Estado
const fecha = ref('')
const areaId = ref<number | null>(null)
const areas = ref<any[]>([])
const citasPreview = ref<CitaConfirmadaResponse | null>(null)
const loadingPreview = ref(false)
const loadingPDF = ref(false)
const error = ref('')

// Inicializar fecha con hoy
onMounted(async () => {
  const hoy = new Date()
  fecha.value = hoy.toISOString().split('T')[0]
  
  // Cargar áreas
  try {
    const { data } = await areaService.getAreas()
    areas.value = data
  } catch (err) {
    console.error('Error al cargar áreas:', err)
  }
})

// Limpiar preview cuando cambian los filtros
watch([fecha, areaId], () => {
  citasPreview.value = null
  error.value = ''
})

// Ver vista previa
const verVistaPrevia = async () => {
  if (!fecha.value || !areaId.value) return
  
  loadingPreview.value = true
  error.value = ''
  
  try {
    const { data } = await citaService.getCitasConfirmadas({
      fecha: fecha.value,
      area_id: areaId.value
    })
    citasPreview.value = data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Error al obtener citas'
    citasPreview.value = null
  } finally {
    loadingPreview.value = false
  }
}

// Descargar PDF
const descargarPDF = async () => {
  if (!fecha.value || !areaId.value) return
  
  loadingPDF.value = true
  error.value = ''
  
  try {
    const response = await citaService.descargarPDFCitasConfirmadas({
      fecha: fecha.value,
      area_id: areaId.value
    })
    
    // Crear URL del blob y descargar
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    
    // Crear enlace temporal para descarga
    const link = document.createElement('a')
    link.href = url
    
    // Obtener nombre del área para el archivo
    const areaNombre = areas.value.find(a => a.id === areaId.value)?.nombre || 'area'
    const nombreLimpio = areaNombre.toLowerCase().replace(/\s+/g, '_').normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    link.download = `citas_confirmadas_${nombreLimpio}_${fecha.value}.pdf`
    
    document.body.appendChild(link)
    link.click()
    
    // Limpiar
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Error al generar PDF'
  } finally {
    loadingPDF.value = false
  }
}

// Cerrar modal
const cerrar = () => {
  emit('close')
  citasPreview.value = null
  error.value = ''
}
</script>
```

---

## 4. Integrar en AdminCitas.vue

Agregar botón de imprimir y el modal:

```vue
<!-- En la sección de acciones del header de AdminCitas.vue -->
<template>
  <div class="flex items-center gap-3">
    <!-- Otros botones... -->
    
    <!-- Botón Imprimir Citas -->
    <button 
      @click="modalImprimirVisible = true"
      class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition"
    >
      <i class="pi pi-print"></i>
      Imprimir Citas
    </button>
  </div>
  
  <!-- Al final del template -->
  <ModalImprimirCitas 
    :visible="modalImprimirVisible" 
    @close="modalImprimirVisible = false" 
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ModalImprimirCitas from '@/components/modals/ModalImprimirCitas.vue'

const modalImprimirVisible = ref(false)
// ... resto del script
</script>
```

---

## 5. Opción Alternativa: Botón Directo (Sin Modal)

Si prefieres una implementación más simple sin modal:

```vue
<template>
  <div class="flex items-center gap-4 p-4 bg-white rounded-xl shadow">
    <div class="flex-1">
      <label class="text-sm text-gray-600">Fecha:</label>
      <input type="date" v-model="fechaImprimir" class="ml-2 px-3 py-1 border rounded-lg" />
    </div>
    <div class="flex-1">
      <label class="text-sm text-gray-600">Área:</label>
      <select v-model="areaImprimir" class="ml-2 px-3 py-1 border rounded-lg">
        <option :value="null">Seleccione</option>
        <option v-for="area in areas" :key="area.id" :value="area.id">{{ area.nombre }}</option>
      </select>
    </div>
    <button 
      @click="descargarPDFRapido"
      :disabled="!fechaImprimir || !areaImprimir || descargando"
      class="px-6 py-2 bg-blue-600 text-white rounded-xl disabled:opacity-50 flex items-center gap-2"
    >
      <i :class="descargando ? 'pi pi-spin pi-spinner' : 'pi pi-download'"></i>
      {{ descargando ? 'Generando...' : 'Descargar PDF' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import citaService from '@/services/citaService'

const fechaImprimir = ref('')
const areaImprimir = ref<number | null>(null)
const descargando = ref(false)
const areas = ref<any[]>([]) // Cargar desde areaService

const descargarPDFRapido = async () => {
  if (!fechaImprimir.value || !areaImprimir.value) return
  
  descargando.value = true
  try {
    const response = await citaService.descargarPDFCitasConfirmadas({
      fecha: fechaImprimir.value,
      area_id: areaImprimir.value
    })
    
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `citas_${fechaImprimir.value}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    alert('Error al generar PDF')
  } finally {
    descargando.value = false
  }
}
</script>
```

---

## 6. Contenido del PDF Generado

El PDF incluye:

| Elemento | Descripción |
|----------|-------------|
| **Encabezado** | "CENTRO DE SALUD" + "Lista de Citas Confirmadas" |
| **Información** | Área, Fecha (en español), Total de citas |
| **Tabla** | N°, DNI, Nombre Completo, Horario, Turno |
| **Estilos** | Colores alternados, encabezado azul, diseño profesional |
| **Pie de página** | Fecha y hora de generación |

### Orden de las citas:
Las citas se ordenan por **fecha de registro** (ascendente), lo que significa que el paciente que registró su cita primero aparecerá con el número 1.

---

## 7. Ejemplo de Respuesta JSON

```json
{
  "success": true,
  "fecha": "2025-12-11",
  "area": {
    "id": 1,
    "nombre": "Medicina General"
  },
  "total": 3,
  "citas": [
    {
      "numero": 1,
      "id": 45,
      "paciente": {
        "id": 12,
        "nombres": "Juan Carlos",
        "apellido_paterno": "García",
        "apellido_materno": "López",
        "dni": "12345678",
        "telefono": "987654321"
      },
      "horario": {
        "id": 5,
        "hora_inicio": "07:30:00",
        "hora_fin": "13:30:00",
        "turno": "M",
        "turno_nombre": "Mañana"
      },
      "fecha_registro": "2025-12-10T14:30:00"
    }
  ]
}
```

---

## 8. Pruebas Rápidas

### Con cURL:
```bash
# Ver JSON
curl "http://localhost:5000/api/citas/confirmadas?fecha=2025-12-11&area_id=1"

# Descargar PDF
curl "http://localhost:5000/api/citas/confirmadas/pdf?fecha=2025-12-11&area_id=1" -o citas.pdf
```

### En el navegador:
Abrir directamente:
```
http://localhost:5000/api/citas/confirmadas/pdf?fecha=2025-12-11&area_id=1
```

---

## 11. ACTUALIZACIÓN: Filtro por Médico

Se ha agregado la opción de filtrar por médico específico, ya que un área puede tener varios doctores.

### 1. Actualizar `citaService.ts`

Agregar `medico_id` opcional a los parámetros:

```typescript
export interface CitaConfirmadaParams {
  fecha: string;
  area_id: number;
  medico_id?: number | null; // Nuevo campo opcional
}
```

### 2. Actualizar componente `ModalImprimirCitas.vue`

Agregar el selector de médicos que se actualiza al cambiar el área.

```vue
<!-- Agregar debajo del selector de Área -->
<div v-if="areaId">
  <label class="block text-sm font-semibold text-gray-700 mb-2">
    <i class="pi pi-user-md mr-1 text-blue-600"></i>
    Médico (Opcional)
  </label>
  <select 
    v-model="medicoId" 
    class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
  >
    <option :value="null">Todos los médicos del área</option>
    <option v-for="medico in medicosFiltrados" :key="medico.id" :value="medico.id">
      {{ medico.name }}
    </option>
  </select>
  <p class="text-xs text-gray-500 mt-1 pl-1">
    Si no selecciona uno, se mostrarán todos los médicos en la tabla.
  </p>
</div>
```

### 3. Lógica del Componente (Script)

```typescript
import usuarioService from '@/services/usuarioService' // Asegúrate de tener este servicio

// Estado
const medicoId = ref<number | null>(null)
const medicos = ref<any[]>([])
const medicosFiltrados = ref<any[]>([])

// Cargar todos los médicos al montar
onMounted(async () => {
    // ... carga inicial ...
    try {
        const { data } = await usuarioService.getMedicos()
        medicos.value = data
    } catch (e) { console.error(e) }
})

// Filtrar médicos cuando cambia el área
watch(areaId, (newId) => {
    medicoId.value = null // Resetear médico seleccionado
    if (newId) {
        // Asumiendo que el objeto médico tiene area_id o lista de areas
        // Si no tienes esa info en getMedicos(), deberías llamar a un endpoint 
        // como /api/horarios/medicos-por-area?area_id=X
        
        // Opción simple: si tu lista de usuarios tiene el rol y area asignada
        medicosFiltrados.value = medicos.value.filter(m => m.area_id === newId) 
    } else {
        medicosFiltrados.value = []
    }
})

// Actualizar llamadas al servicio
const generarPDF = () => {
    citaService.descargarPDFCitasConfirmadas({
        fecha: fecha.value,
        area_id: areaId.value,
        medico_id: medicoId.value // Pasar el valor
    })
}
```

### Resultado en el PDF:

1. **Si selecciona médico**: Aparece "Médico: Dr. Juan Pérez" en el encabezado y la tabla es exclusiva de sus citas.
2. **Si NO selecciona médico**: La tabla incluye una columna extra "Médico Asignado" para saber quién atiende cada cita.

---

## 9. Resumen de Archivos a Modificar

| Archivo | Acción |
|---------|--------|
| `src/services/citaService.ts` | Agregar interfaces y métodos |
| `src/components/modals/ModalImprimirCitas.vue` | Crear nuevo componente |
| `src/views/admin/AdminCitas.vue` | Agregar botón e importar modal |

---

## 10. Notas Importantes

1. **responseType: 'blob'**: Es crucial para recibir archivos binarios como PDFs.

2. **Nombres de archivo**: Se sanitizan caracteres especiales (tildes, espacios) para compatibilidad.

3. **Manejo de errores**: Si el área no existe o no hay citas, el endpoint retorna JSON con el error (no PDF).

4. **Actualización en tiempo real**: Si se confirman más citas después de generar el PDF, se debe generar uno nuevo.
