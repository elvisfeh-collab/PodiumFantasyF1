// Inicializa Supabase con tus credenciales de tu proyecto evitando colisiones globales
const SUPABASE_URL = 'https://tobebpyymtwchqjfchip.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_F-J01J3ktvXhYofc3N0eYA_lhhKBwWB';

// Usamos un nombre de instancia único para el cliente
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Función para registrar un nuevo usuario
async function manejarRegistro(event) {
    event.preventDefault();

    // Capturar los valores del formulario HTML
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const username = document.getElementById('reg-username').value;
    const pais = document.getElementById('reg-pais').value;
    const idioma = document.getElementById('reg-idioma').value || 'es';

    try {
        // Paso 1: Registrar el usuario en la autenticación de Supabase Auth
        const { data: authData, error: authError } = await supabase.auth.signUp({
            email: email,
            password: password
        });

        if (authError) throw authError;

        const userId = authData.user.id; // El UUID generado por Supabase Auth

        // Paso 2: Insertar los datos complementarios en tu tabla personalizada 'usuarios'
        const { error: profileError } = await supabase
            .from('usuarios')
            .insert([
                { 
                    id: userId, 
                    username: username, 
                    pais: pais, 
                    idioma_preferido: idioma, 
                    puntos_globales: 0,
                    escuderia_id: null // Se queda nulo hasta que decidas activar las escuderías
                }
            ]);

        if (profileError) throw profileError;

        alert('¡Registro exitoso, socio! Bienvenido a Podium Fantasy F1.');
        // Redirigir al Dashboard o limpiar formulario

    } catch (error) {
        console.error('Error en el registro:', error.message);
        alert('Hubo un error al registrarse: ' + error.message);
    }
}
