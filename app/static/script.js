// 右侧目录跟随滚动
document.addEventListener('DOMContentLoaded', function () {
    const sections = document.querySelectorAll('.content-main > div');
    const menuLinks = document.querySelectorAll('.menu-list a');
    const sidebar = document.querySelector('.content-sidebar');

    const makeActive = (link) => menuLinks[link].classList.add("is-active");
    const removeActive = (link) => menuLinks[link].classList.remove("is-active");
    const removeAllActive = () => [...Array(sections.length).keys()].forEach((link) => removeActive(link));

    let currentActive = 0;

    window.addEventListener('scroll', () => {
        let currentSectionIndex = sections.length - [...sections].reverse().findIndex((section) => window.scrollY >= section.offsetTop - 50) - 1;
        currentSectionIndex = currentSectionIndex >= sections.length ? sections.length - 1 : currentSectionIndex;

        if (currentSectionIndex !== currentActive) {
            removeAllActive();
            currentActive = currentSectionIndex;
            makeActive(currentActive);
            
            // 获取活跃目录项及其相对于sidebar的位置
            const activeElement = menuLinks[currentActive];
            if (activeElement) {
                const activeElementOffset = activeElement.offsetTop + activeElement.offsetHeight;
                const sidebarHeight = sidebar.offsetHeight;

                // 判断活跃目录项是否超出sidebar的可见范围
                if (activeElementOffset > sidebar.scrollTop + sidebarHeight || activeElementOffset < sidebar.scrollTop) {
                    // 将活跃目录项滚动到sidebar的中央位置
                    sidebar.scrollTop = activeElementOffset - sidebarHeight / 2 - activeElement.offsetHeight / 2;
                }
            }
        }
    });
});