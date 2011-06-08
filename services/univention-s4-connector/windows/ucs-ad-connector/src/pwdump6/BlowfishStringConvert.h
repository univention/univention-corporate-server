
	void ConvertToBlowfishLongs(char* string, DWORD* L, DWORD* R)
	{
		*L = *((int*)(string + 0));
		*R = *((int*)(string + 4)); 
	}

	void ConvertToBlowfishLongsWide(wchar_t* string, DWORD* L, DWORD* R)
	{
		*L = *((int*)(string + 0));
		*R = *((int*)(string + 2)); 
	}

	void ConvertFromBlowfishLongs(DWORD L, DWORD R, char* string)
	{
		*((int*)(string + 0)) = L;
		*((int*)(string + 4)) = R; 
	}

