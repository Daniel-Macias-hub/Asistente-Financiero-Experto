# Asistente Financiero ESP32

Este proyecto contiene el firmware para el Asistente Financiero Multimodal basado en ESP32.

## Estructura de Archivos Principales

- **`config.h`**: Contiene la configuración general del proyecto (versiones, baudrate, etc.).
- **`pins.h`**: Define las asignaciones de pines para los periféricos conectados al ESP32 (pantalla OLED, micrófono I2S, bocina I2S, etc.).
- **`secrets.h`**: Almacena las credenciales de la red WiFi (nombre de red y contraseña). Este archivo no debe compartirse públicamente si contiene claves reales.

## Pruebas de Periféricos

La carpeta `pruebas/` contiene ejemplos independientes para verificar cada uno de los componentes:

1. **`01_Blink`**: Prueba del LED integrado en la placa.
2. **`02_OLED`**: Prueba de inicialización y despliegue gráfico en la pantalla.
3. **`03_Microfono`**: Captura de audio usando el micrófono I2S.
4. **`04_Bocina`**: Salida de audio usando la bocina I2S.
5. **`05_WiFi`**: Conexión a red local e Internet.
6. **`06_API`**: Consultas externas a servicios web/APIs.
7. **`07_Completo`**: Integración final de todos los módulos.
