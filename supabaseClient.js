// Inicializa Supabase con tus credenciales de tu proyecto
const SUPABASE_URL = 'https://tobebpyymtwchqjfchip.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_F-J01J3ktvXhYofc3N0eYA_lhhKBwWB';

// Renombrado a supabaseClient para evitar colisiones con el CDN
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Función para registrar un nuevo usuario
async function manejarRegistro(event) {
    event.preventDefault();

    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const username = document.getElementById('reg-username').value;
    const pais = document.getElementById('reg-pais').value;
    const idioma = document.getElementById('reg-idioma').value || 'es';

    try {
        const { data: authData, error: authError } = await supabaseClient.auth.signUp({
            email: email,
            password: password
        });

        if (authError) throw authError;

        const userId = authData.user.id; 

        const { error: profileError } = await supabaseClient
            .from('usuarios')
            .insert([
                { 
                    id: userId, 
                    username: username, 
                    pais: pais, 
                    idioma_preferido: idioma, 
                    puntos_globales: 0,
                    escuderia_id: null 
                }
            ]);

        if (profileError) throw profileError;

        alert('¡Registro exitoso, socio! Bienvenido a Podium Fantasy F1.');

    } catch (error) {
        console.error('Error en el registro:', error.message);
        alert('Hubo un error al registrarse: ' + error.message);
    }
}
