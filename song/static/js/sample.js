
 
  const audioPlayers = document.querySelectorAll('.audio-player');
 
  audioPlayers.forEach((audioPlayer) => {
    const audio = audioPlayer.querySelector('audio')
    audio.volume = .3;
    const toggleBtn = audioPlayer.querySelector('.toggle');
 
    // 音声データを再生する非同期関数
    async function playAudio() {
      try {
        await audio.play();
      } catch (err) {
        console.warn(err)
      }
    }
 
    toggleBtn.addEventListener('click', () => {
      if (audio.paused) {
        // 上記で定義した関数を呼び出す
        playAudio();
      } else {
        audio.pause();
      }
    });
 
    // pause イベントでボタンのラベルを変更
    audio.addEventListener('pause', () => {
      toggleBtn.textContent = 'Play';
    });
 
    // play イベントでボタンのラベルを変更
    audio.addEventListener('play', () => {
      toggleBtn.textContent = 'Pause';
    });
 
    // ended イベントでボタンのラベルを変更
    audio.addEventListener('ended', () => {
      toggleBtn.textContent = 'Play';
    });
 
  });
